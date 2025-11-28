export JAVA_HOME:=$(HOME)/android-studio/jbr
export ANDROID_HOME:=$(HOME)/Android/Sdk
export JSON_JAR=bin/json.jar
export JSON_JAR_URL=https://repo1.maven.org/maven2/org/json/json/20250517/json-20250517.jar
export FORMAT_JAR=bin/google-java-format.jar
export FORMAT_JAR_URL=https://github.com/google/google-java-format/releases/download/v1.32.0/google-java-format-1.32.0-all-deps.jar
export PATH:=$(PATH):$(ANDROID_HOME)/platform-tools:$(ANDROID_HOME)/tools

DICT_RES:=android/app/src/main/res/raw/dictionary_jsonl
ENGITA_JAR_SRC:=android/app/src/main/java/net/mdln/engita/Dict.java android/app/src/main/java/net/mdln/engita/Term.java cli/net/mdln/engita/Main.java
ENGITA_JAR:=cli/build/engita.jar

all: build

emulator:
	$(HOME)/Android/Sdk/emulator/emulator -avd Medium_Phone_API_36.1

build: $(DICT_RES)
	cd android && ./gradlew assembleDebug

install: $(DICT_RES)
	cd android && ./gradlew installDebug

run:
	cd android && $(ANDROID_HOME)/platform-tools/adb shell am start -n net.mdln.engita/.MainActivity

logcat:
	cd android && $(ANDROID_HOME)/platform-tools/adb logcat

test:
	cd android && ./gradlew connectedAndroidTest

$(FORMAT_JAR):
	mkdir -p bin && curl -sfL -o "$(FORMAT_JAR)" "$(FORMAT_JAR_URL)"

$(JSON_JAR):
	mkdir -p bin && curl -sfL -o "$(JSON_JAR)" "$(JSON_JAR_URL)"

fmt: $(FORMAT_JAR)
	find . -name "*.java" | xargs "$(JAVA_HOME)/bin/java" -jar "$(FORMAT_JAR)" --replace
	for f in dict/dictionary-delete.csv dict/dictionary-modify.csv ; do sort $$f > $$f.sorted && mv $$f.sorted $$f ; done
	ruff check . --fix
	ruff format .

bundle: $(DICT_RES)
	@bash -c 'read -s -p "Keystore password: " KEYSTORE_PASSWORD && echo && \
	export KEYSTORE_PASSWORD && export KEY_PASSWORD=$$KEYSTORE_PASSWORD && \
	cd android && ./gradlew bundleRelease'

$(DICT_RES): dict/dictionary.jsonl
	mkdir -p $$(dirname $@) && cp -f $< $@

cli: $(ENGITA_JAR)

$(ENGITA_JAR): $(ENGITA_JAR_SRC) $(DICT_RES) $(JSON_JAR)
	$(JAVA_HOME)/bin/javac -cp $(JSON_JAR) -d cli/build $(ENGITA_JAR_SRC)
	$(JAVA_HOME)/bin/jar cfe $@ net.mdln.engita.Main -C cli/build . -C android/app/src/main/res/raw .

runcli: $(ENGITA_JAR)
	$(JAVA_HOME)/bin/java -cp $(ENGITA_JAR):$(JSON_JAR) net.mdln.engita.Main "$(WORD)"

clean:
	rm -rf android/build android/app/src/main/res/raw/* android/.gradle cli/build dict/__pycache__
