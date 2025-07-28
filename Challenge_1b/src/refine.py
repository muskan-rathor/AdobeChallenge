from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.summarizers.lsa import LsaSummarizer

_summarizer = LsaSummarizer()
def refine(text: str, sentences: int = 2) -> str:
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summary = _summarizer(parser.document, sentences)
    return " ".join(str(s) for s in summary)