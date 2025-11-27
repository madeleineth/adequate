package net.mdln.engita;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
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
    if (query.isEmpty() || !query.matches("^[a-zA-Z' ]+$")) {
      return new ArrayList<>();
    }
    // Short queries require full-word match; longer queries allow prefix match
    // on words.
    String patternStr =
        query.length() <= 2
            ? "\"[^\"]*\\b" + Pattern.quote(query) + "\\b[^\"]*\""
            : "\"[^\"]*\\b" + Pattern.quote(query);
    Pattern pattern = Pattern.compile(patternStr, Pattern.CASE_INSENSITIVE);
    Matcher matcher = pattern.matcher(dictionaryJsonl);
    List<Term> results = new ArrayList<>();
    int lastLineStart = -1;
    while (matcher.find() && results.size() < maxResults) {
      int matchStart = matcher.start();
      int lineStart = dictionaryJsonl.lastIndexOf('\n', matchStart - 1) + 1;
      int lineEnd = dictionaryJsonl.indexOf('\n', matchStart);
      if (lineEnd == -1) {
        lineEnd = dictionaryJsonl.length();
      }
      if (lineStart == lastLineStart) { // skip multiple same-line matches
        continue;
      }
      lastLineStart = lineStart;
      String line = dictionaryJsonl.substring(lineStart, lineEnd);
      results.add(parseLine(line));
    }
    return results;
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
