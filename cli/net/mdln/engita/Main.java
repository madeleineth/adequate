package net.mdln.engita;

import java.util.List;

public class Main {
  static final String DICT_RES = "/dictionary_jsonl";

  public static void main(String[] args) {
    if (args.length != 1) {
      System.err.println("Usage: java -cp ... net.mdln.engita.Main <query>");
      System.exit(1);
    }
    String query = args[0];
    Dict dict = Dict.fromStream(Main.class.getResourceAsStream(DICT_RES));
    List<Term> results = dict.search(query, 100);
    if (results.isEmpty()) {
      System.out.println("No results found for: " + query);
      return;
    }
    for (Term term : results) {
      System.out.println(term.root + "," + term.forms + "," + term.pos + "," + term.translation);
      term.conjugations.forEach(
          (tense, forms) -> {
            System.out.println("  conj:" + tense + "," + forms);
          });
    }
  }
}
