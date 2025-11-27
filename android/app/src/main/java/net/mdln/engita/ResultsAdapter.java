package net.mdln.engita;

import android.app.AlertDialog;
import android.text.Html;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.ArrayList;
import java.util.List;

class ResultsAdapter extends RecyclerView.Adapter<ResultsAdapter.ViewHolder> {
  private List<Term> terms = new ArrayList<>();

  static class ViewHolder extends RecyclerView.ViewHolder {
    public final TextView termText;
    public final TextView definitionText;

    public ViewHolder(View view) {
      super(view);
      this.termText = view.findViewById(R.id.term_text);
      this.definitionText = view.findViewById(R.id.definition_text);
    }
  }

  void setTerms(List<Term> terms) {
    this.terms = terms;
    notifyDataSetChanged();
  }

  @NonNull
  @Override
  public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
    View view =
        LayoutInflater.from(parent.getContext()).inflate(R.layout.result_item, parent, false);
    return new ViewHolder(view);
  }

  @Override
  public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
    Term term = terms.get(position);

    String termHtml;
    if (term.pos.equals("v")) {
      termHtml = "<b>" + term.root + "</b>";
    } else {
      termHtml = "<b>" + term.forms.replace("/", ", ") + "</b>";
    }
    holder.termText.setText(Html.fromHtml(termHtml, Html.FROM_HTML_MODE_COMPACT));
    String defHtml = "<i>" + term.pos + "</i> " + term.translation;
    holder.definitionText.setText(Html.fromHtml(defHtml, Html.FROM_HTML_MODE_COMPACT));

    if (!term.conjugations.isEmpty()) {
      holder.itemView.setOnClickListener(v -> showConjugationDialog(holder, term));
    } else {
      holder.itemView.setOnClickListener(null);
    }
  }

  private void showConjugationDialog(ViewHolder holder, Term term) {
    StringBuilder message = new StringBuilder();
    term.conjugations.forEach(
        (tense, forms) -> {
          String[] formArray = forms.split("/");
          message.append(tense.name().toUpperCase()).append(":\n");
          String[] labels = {"1sg", "2sg", "3sg", "1pl", "2pl", "3pl"};
          for (int i = 0; i < formArray.length && i < labels.length; i++) {
            if (!formArray[i].isEmpty()) {
              message.append("  ").append(labels[i]).append(": ").append(formArray[i]).append("\n");
            }
          }
          message.append("\n");
        });
    new AlertDialog.Builder(holder.itemView.getContext())
        .setTitle(term.root)
        .setMessage(message.toString())
        .setPositiveButton("OK", null)
        .show();
  }

  @Override
  public int getItemCount() {
    return terms.size();
  }
}
