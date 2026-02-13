TEX=main

.PHONY: all pdf clean

all: pdf

pdf:
	xelatex -interaction=nonstopmode -halt-on-error $(TEX).tex
	biber $(TEX)
	xelatex -interaction=nonstopmode -halt-on-error $(TEX).tex
	xelatex -interaction=nonstopmode -halt-on-error $(TEX).tex

clean:
	rm -f $(TEX).aux $(TEX).bbl $(TEX).bcf $(TEX).blg $(TEX).log $(TEX).nav $(TEX).out $(TEX).run.xml $(TEX).snm $(TEX).toc $(TEX).vrb
