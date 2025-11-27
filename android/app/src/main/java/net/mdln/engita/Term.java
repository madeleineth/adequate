package net.mdln.engita;

import java.util.SortedMap;

class Term {
  enum SimpleTense {
    PRESENT,
    IMPERFECT
  }

  final String root;
  final String forms; // /-separated alternative forms
  final String pos;
  final String translation;
  final SortedMap<SimpleTense, String> conjugations; // /-separated forms

  public Term(
      String root,
      String forms,
      String pos,
      String translation,
      SortedMap<SimpleTense, String> conjugations) {
    if (root == null
        || forms == null
        || pos == null
        || translation == null
        || conjugations == null) {
      throw new NullPointerException();
    }
    this.root = root;
    this.forms = forms;
    this.pos = pos;
    this.translation = translation;
    this.conjugations = conjugations;
  }
}
