package net.mdln.engita;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

public class Main {
  static final String DICT_RES = "/dictionary_jsonl";

  public static void main(String[] args) throws Exception {
    if (args.length == 0) {
      System.err.println("Usage: java -cp ... net.mdln.engita.Main query...");
      System.exit(1);
    }
    Dict dict = Dict.fromStream(Main.class.getResourceAsStream(DICT_RES), 100);

    int threads = Runtime.getRuntime().availableProcessors();
    ExecutorService pool = Executors.newFixedThreadPool(threads);
    List<Future<List<Term>>> futures = new ArrayList<>();
    for (String query : args) {
      futures.add(pool.submit(() -> dict.search(query)));
    }
    pool.shutdown();

    for (int i = 0; i < args.length; i++) {
      String query = args[i];
      List<Term> results = futures.get(i).get();
      System.out.println("[" + query + "] " + results.size() + " results");
      for (Term term : results) {
        System.out.println(term.root + "," + term.forms + "," + term.pos + "," + term.translation);
        term.conjugations.forEach(
            (tense, forms) -> {
              System.out.println("  conj:" + tense + "," + forms);
            });
      }
    }
  }
}
