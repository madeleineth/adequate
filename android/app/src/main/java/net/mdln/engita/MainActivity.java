package net.mdln.engita;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.SearchView;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;

public class MainActivity extends AppCompatActivity {
  private static final int MAX_RESULTS = 50;

  private ResultsAdapter resultsAdapter;
  private SearchView searchBox;
  private TextView footerLink;
  private Dict dict;

  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    setContentView(R.layout.activity_main);

    this.dict =
        Dict.fromStream(getResources().openRawResource(R.raw.dictionary_jsonl), MAX_RESULTS);

    this.searchBox = findViewById(R.id.search_box);
    this.footerLink = findViewById(R.id.footer_link);
    this.footerLink.setOnClickListener(
        v -> {
          Intent intent =
              new Intent(Intent.ACTION_VIEW, Uri.parse("https://github.com/madeleineth/adequate"));
          startActivity(intent);
        });

    ViewCompat.setOnApplyWindowInsetsListener(
        findViewById(android.R.id.content),
        (v, insets) -> {
          Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
          v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
          return insets;
        });
    this.resultsAdapter = new ResultsAdapter();
    RecyclerView recyclerView = findViewById(R.id.search_results);
    recyclerView.setAdapter(this.resultsAdapter);
    recyclerView.setLayoutManager(new LinearLayoutManager(this));

    this.searchBox.setOnQueryTextListener(
        new SearchView.OnQueryTextListener() {
          @Override
          public boolean onQueryTextChange(String text) {
            performSearch(text);
            return true;
          }

          @Override
          public boolean onQueryTextSubmit(String text) {
            performSearch(text);
            return true;
          }
        });

    searchBox.requestFocus();
  }

  private void performSearch(String query) {
    List<Term> results = dict.search(query);
    resultsAdapter.setTerms(results);
    footerLink.setVisibility(results.isEmpty() ? View.VISIBLE : View.GONE);
  }
}
