import nltk

print("Downloading all required AI models...")

resources = [
    "punkt",
    "punkt_tab",                        # <--- The one causing issues before
    "stopwords",
    "vader_lexicon",
    "averaged_perceptron_tagger",
    "averaged_perceptron_tagger_eng",   # <--- The specific english version
    "maxent_ne_chunker",
    "maxent_ne_chunker_tab",            # <--- The one causing the NEW error
    "words"
]

for r in resources:
    try:
        print(f"Downloading {r}...")
        nltk.download(r)
    except Exception as e:
        print(f"Error downloading {r}: {e}")

print("\n✅ Success! All AI models are downloaded.")



#   Who are our main competitors?
#   How much funding did we get?