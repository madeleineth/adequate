package net.mdln.engita;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.SortedMap;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.json.JSONException;
import org.json.JSONObject;

class Dict {
  private final String dictionaryJsonl;

  Dict(String dictionaryJsonl) {
    this.dictionaryJsonl = dictionaryJsonl;
  }

  static Dict fromStream(InputStream stream) {
    StringBuilder sb = new StringBuilder();
    try (InputStreamReader isr = new InputStreamReader(stream, "UTF-8");
        BufferedReader reader = new BufferedReader(isr)) {
      String line;
      while ((line = reader.readLine()) != null) {
        sb.append(line).append("\n");
      }
    } catch (IOException e) {
      throw new RuntimeException("Failed to read stream", e);
    }
    return new Dict(sb.toString());
  }

  List<Term> search(String query, int maxResults) {
    query = query.trim().toLowerCase();
    if (query.isEmpty() || !query.matches("^[a-zA-ZàèéìòùÀÈÉÌÒÙ' ]+$")) {
      return new ArrayList<>();
    }

    // Pattern to find candidate lines containing the query (accent-insensitive)
    String containsPattern = buildAccentInsensitivePattern(query);
    Pattern pattern = Pattern.compile(containsPattern, Pattern.CASE_INSENSITIVE);

    List<Term> exactMatches = new ArrayList<>();
    List<Term> prefixMatches = new ArrayList<>();
    Set<String> seen = new HashSet<>();

    Matcher matcher = pattern.matcher(dictionaryJsonl);
    int lastLineStart = -1;

    while (matcher.find() && (exactMatches.size() + prefixMatches.size()) < maxResults) {
      int matchStart = matcher.start();
      int lineStart = dictionaryJsonl.lastIndexOf('\n', matchStart - 1) + 1;
      int lineEnd = dictionaryJsonl.indexOf('\n', matchStart);
      if (lineEnd == -1) {
        lineEnd = dictionaryJsonl.length();
      }
      if (lineStart == lastLineStart) {
        continue;
      }
      lastLineStart = lineStart;

      String line = dictionaryJsonl.substring(lineStart, lineEnd);
      Term term = parseLine(line);
      String key = term.root + "\0" + term.pos;
      if (seen.contains(key)) {
        continue;
      }
      seen.add(key);

      if (isExactMatch(term, query)) {
        exactMatches.add(term);
      } else if (query.length() > 2 && isPrefixMatch(term, query)) {
        prefixMatches.add(term);
      } else if (query.length() <= 2) {
        // Short queries only get exact matches, skip non-exact
      }
    }

    Collections.sort(exactMatches, (a, b) -> a.root.compareTo(b.root));
    Collections.sort(prefixMatches, (a, b) -> a.root.compareTo(b.root));

    List<Term> results = new ArrayList<>(exactMatches);
    results.addAll(prefixMatches);
    return results;
  }

  /** Check if query exactly matches root, any form, any translation, or any conjugation. */
  private boolean isExactMatch(Term term, String query) {
    String normalizedQuery = normalizeAccents(query);
    if (normalizeAccents(term.root).equalsIgnoreCase(normalizedQuery)) {
      return true;
    }
    for (String form : term.forms.split("/")) {
      if (normalizeAccents(form).equalsIgnoreCase(normalizedQuery)) {
        return true;
      }
    }
    for (String trans : term.translation.split("/")) {
      if (normalizeAccents(trans).equalsIgnoreCase(normalizedQuery)) {
        return true;
      }
    }
    for (String conj : term.conjugations.values()) {
      for (String form : conj.split("/")) {
        if (normalizeAccents(form).equalsIgnoreCase(normalizedQuery)) {
          return true;
        }
      }
    }
    return false;
  }

  /** Check if query is a word prefix in root, forms, or translation. */
  private boolean isPrefixMatch(Term term, String query) {
    String q = normalizeAccents(query.toLowerCase());
    if (startsWithWord(normalizeAccents(term.root.toLowerCase()), q)) {
      return true;
    }
    for (String form : term.forms.split("/")) {
      if (startsWithWord(normalizeAccents(form.toLowerCase()), q)) {
        return true;
      }
    }
    for (String trans : term.translation.split("/")) {
      if (startsWithWord(normalizeAccents(trans.toLowerCase()), q)) {
        return true;
      }
    }
    return false;
  }

  /** Check if text starts with prefix at a word boundary. */
  private boolean startsWithWord(String text, String prefix) {
    if (text.startsWith(prefix)) {
      return true;
    }
    // Check for prefix after word boundaries (space, start of word)
    int idx = 0;
    while ((idx = text.indexOf(prefix, idx)) >= 0) {
      if (idx == 0 || !Character.isLetterOrDigit(text.charAt(idx - 1))) {
        return true;
      }
      idx++;
    }
    return false;
  }

  /** Build a regex pattern that matches vowels with or without accents. */
  private String buildAccentInsensitivePattern(String query) {
    StringBuilder sb = new StringBuilder();
    for (char c : query.toCharArray()) {
      switch (c) {
        case 'a':
        case 'à':
          sb.append("[aà]");
          break;
        case 'e':
        case 'è':
        case 'é':
          sb.append("[eèé]");
          break;
        case 'i':
        case 'ì':
          sb.append("[iì]");
          break;
        case 'o':
        case 'ò':
          sb.append("[oò]");
          break;
        case 'u':
        case 'ù':
          sb.append("[uù]");
          break;
        default:
          sb.append(c);
          break;
      }
    }
    return sb.toString();
  }

  /** Normalize accented characters to their base form for comparison. */
  private String normalizeAccents(String text) {
    return text.replace('à', 'a')
        .replace('è', 'e')
        .replace('é', 'e')
        .replace('ì', 'i')
        .replace('ò', 'o')
        .replace('ù', 'u')
        .replace('À', 'A')
        .replace('È', 'E')
        .replace('É', 'E')
        .replace('Ì', 'I')
        .replace('Ò', 'O')
        .replace('Ù', 'U');
  }

  private Term parseLine(String line) {
    try {
      JSONObject json = new JSONObject(line);
      String root = json.getString("r");
      String forms = json.optString("f", "");
      String pos = json.getString("p");
      String translation = json.getString("t");
      SortedMap<Term.SimpleTense, String> conjugations = new TreeMap<>();
      if (json.has("c")) {
        JSONObject conjJson = json.getJSONObject("c");
        for (Term.SimpleTense tense : Term.SimpleTense.values()) {
          String key = tense.name().toLowerCase();
          if (conjJson.has(key)) {
            conjugations.put(tense, conjJson.getString(key));
          }
        }
      }
      return new Term(root, forms, pos, translation, conjugations);
    } catch (JSONException e) {
      throw new RuntimeException("Error parsing: " + line, e);
    }
  }
}
