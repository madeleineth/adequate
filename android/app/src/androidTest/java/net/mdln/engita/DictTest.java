package net.mdln.engita;

import static org.junit.Assert.assertEquals;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public class DictTest {

  @Test
  public void searchFindsConjugation() {
    String jsonl =
        "{\"r\":\"essere\",\"f\":\"\",\"p\":\"v\",\"t\":\"to be\","
            + "\"c\":{\"present\":\"sono/sei/è/siamo/siete/sono\","
            + "\"imperfect\":\"ero/eri/era/eravamo/eravate/erano\"}}\n";
    Dict dict = Dict.fromStream(new ByteArrayInputStream(jsonl.getBytes(StandardCharsets.UTF_8)));
    List<Term> results = dict.search("essere", 10);
    assertEquals(1, results.size());
    Term term = results.get(0);
    assertEquals("essere", term.root);
    assertEquals("v", term.pos);
    assertEquals("to be", term.translation);
    assertEquals("sono/sei/è/siamo/siete/sono", term.conjugations.get(Term.SimpleTense.PRESENT));
    assertEquals(
        "ero/eri/era/eravamo/eravate/erano", term.conjugations.get(Term.SimpleTense.IMPERFECT));
  }
}
