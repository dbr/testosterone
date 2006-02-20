# Makefile to create documentation using the Python LaTeX system.

VERSION=0.4
PYTHON_SRC = /home/whit537/shelf/Python-2.4.2
MKHOWTO    = $(PYTHON_SRC)/Doc/tools/mkhowto \
				--iconserver icons \
				--split 5 \
				--link 2 \
				--favicon icons/zeta.ico \
				--dir ./html \
				--logging \
				--up-link "http://www.zetadev.com/software/testosterone/" \
				--up-title "httpy homepage" \
				--address "<a href=\"http://www.zetadev.com/software/testosterone/\">testosterone is Zeta software</a>. It is copyright &copy; 2006 Chad Whitacre, and is offered free of charge, warranty, and restrictions." \
#				--style style.css


default: html

html: clean
	$(MKHOWTO) testosterone.tex
	cp -r ../icons ./html/
	rm -rf ./html/icons/.svn
	rm -rf ../html && mv ./html ../

pdf:
	$(PYTHON_SRC)/Doc/tools/mkhowto --pdf testosterone.tex
	mv testosterone.pdf ../testosterone-$(VERSION).pdf

clean:
	rm -rf *~ *.aux *.idx *.ilg *.ind *.log *.toc *.bkm *.syn \
			*.pla *.eps *.pdf *.ps *.lof *.l2h *.tex2 *.dvi html
