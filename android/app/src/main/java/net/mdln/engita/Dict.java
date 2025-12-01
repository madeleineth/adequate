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
  private final String normalizedJsonl; // accent-stripped for searching
  private final int maxResults;

  Dict(String dictionaryJsonl, int maxResults) {
    this.dictionaryJsonl = dictionaryJsonl;
    this.normalizedJsonl = normalize(dictionaryJsonl);
    this.maxResults = maxResults;
  }

  static Dict fromStream(InputStream stream, int maxResults) {
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
    return new Dict(sb.toString(), maxResults);
  }

  List<Term> search(String query) {
    query = query.trim().toLowerCase();
    if (!query.matches("^[a-zàèéìòù' ]+$")) {
      return new ArrayList<>();
    }

    String normalizedQuery = normalize(query);
    List<Term> matches = subsearch(normalizedQuery, true /* exact */);
    if (query.length() > 2) {
      matches.addAll(subsearch(normalizedQuery, false /* exact */));
    }
    Set<String> seen = new HashSet<>();
    List<Term> uniqueMatches = new ArrayList<>();
    for (Term t : matches) {
      String key = t.root + "," + t.pos;
      if (!seen.contains(key) && uniqueMatches.size() < this.maxResults) {
        uniqueMatches.add(t);
        seen.add(key);
      }
    }
    return uniqueMatches;
  }

  /** Search for a normalized term, either only exact or only prefix. */
  private List<Term> subsearch(String q, boolean exact) {
    Pattern pattern = Pattern.compile("\\b" + Pattern.quote(q) + (exact ? "\\b" : ""));
    Matcher matcher = pattern.matcher(normalizedJsonl);
    int lastLineStart = -1;
    List<Term> matches = new ArrayList<>();
    while (matcher.find() && matches.size() < this.maxResults) {
      int matchStart = matcher.start();
      int lineStart = this.normalizedJsonl.lastIndexOf('\n', matchStart - 1) + 1;
      int lineEnd = this.normalizedJsonl.indexOf('\n', matchStart);
      if (lineEnd == -1) {
        lineEnd = normalizedJsonl.length();
      }
      if (lineStart == lastLineStart) { // skip multiple matches in the same line
        continue;
      }
      lastLineStart = lineStart;
      // We can use offsets from `normalizedJsonl` in `dictionaryJsonl` because
      // `normalize` preserves string length.
      String line = dictionaryJsonl.substring(lineStart, lineEnd);
      matches.add(parseLine(line));
    }
    Collections.sort(matches, (a, b) -> a.root.compareTo(b.root) * 10 + a.pos.compareTo(b.pos));
    return matches;
  }

  private String normalize(String text) {
    return text.toLowerCase()
        .replace('à', 'a')
        .replace('è', 'e')
        .replace('é', 'e')
        .replace('ì', 'i')
        .replace('ò', 'o')
        .replace('ù', 'u');
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
