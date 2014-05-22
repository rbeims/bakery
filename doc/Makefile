.PHONY: all
all: documentation.html documentation.pdf
html: documentation.html

.PHONY: clean
clean:
	rm -f *.html *.pdf *~

documentation.html: $(wildcard *.txt)
	asciidoc -b html5 documentation.txt

documentation.pdf: $(wildcard *.txt)
	a2x -a docinfo -d book -f pdf --fop documentation.txt
