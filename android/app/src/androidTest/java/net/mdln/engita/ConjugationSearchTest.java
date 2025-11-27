package net.mdln.engita;

import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.RootMatchers.isDialog;
import static androidx.test.espresso.matcher.ViewMatchers.isAssignableFrom;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static org.hamcrest.Matchers.containsString;

import android.view.View;
import android.widget.SearchView;
import androidx.test.espresso.UiController;
import androidx.test.espresso.ViewAction;
import androidx.test.ext.junit.rules.ActivityScenarioRule;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.hamcrest.Matcher;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public class ConjugationSearchTest {

  @Rule
  public ActivityScenarioRule<MainActivity> activityRule =
      new ActivityScenarioRule<>(MainActivity.class);

  public static ViewAction setQuery(final String query) {
    return new ViewAction() {
      @Override
      public Matcher<View> getConstraints() {
        return isAssignableFrom(SearchView.class);
      }

      @Override
      public String getDescription() {
        return "Set query to: " + query;
      }

      @Override
      public void perform(UiController uiController, View view) {
        SearchView searchView = (SearchView) view;
        searchView.setQuery(query, true);
      }
    };
  }

  @Test
  public void searchConjugatedForm() throws InterruptedException {
    activityRule
        .getScenario()
        .onActivity(
            activity -> {
              SearchView searchView = activity.findViewById(R.id.search_box);
              searchView.post(() -> searchView.setQuery("possiamo", false));
            });
    Thread.sleep(1000); // yuck
    onView(withText(containsString("potere"))).perform(click());
    Thread.sleep(300); // yuck
    onView(withText(containsString("può"))).inRoot(isDialog()).check(matches(isDisplayed()));
  }
}
