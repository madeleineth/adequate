export JAVA_HOME:=$(HOME)/android-studio/jbr
export ANDROID_HOME:=$(HOME)/Android/Sdk
export FORMAT_JAR=bin/google-java-format.jar
export FORMAT_JAR_URL=https://github.com/google/google-java-format/releases/download/v1.32.0/google-java-format-1.32.0-all-deps.jar
export PATH:=$(PATH):$(ANDROID_HOME)/platform-tools:$(ANDROID_HOME)/tools

DICT_RES:=android/app/src/main/res/raw/dictionary_csv
CONJ_RES:=android/app/src/main/res/raw/conjugation_csv

all: build

build: $(DICT_RES) $(CONJ_RES)
	cd android && ./gradlew assembleDebug

$(FORMAT_JAR):
	mkdir -p bin && curl -sfL -o "$(FORMAT_JAR)" "$(FORMAT_JAR_URL)"

fmt: $(FORMAT_JAR)
	find . -name "*.java" | xargs "$(JAVA_HOME)/bin/java" -jar "$(FORMAT_JAR)" --replace

clean:
	rm -rf android/build android/app/src/main/res/raw/*_csv
