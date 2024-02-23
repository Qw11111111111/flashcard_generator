Generate flashcards based on pdf-files using llm text processing This is a streamlit app, which generates flashcards based on pdf files. It uses a llm for summarization and a VGG type binary Image classifier. As the Image classifier is trained on data, which was generated by Hand I recommend checking if it makes good predictions for your data. To use the "download to anki" feature of the app you need to have the anki app open in the Background with enabled "AnkiConnect" (connected to WebBindPort 8765). To install AnkiConnect open Anki -> Extensions -> add extension -> paste 2055492159, enable it and restart anki.

To start the program run 
$ git clone https://github.com/Qw11111111111/flashcard_generator.git

then run $ streamlit run main.py