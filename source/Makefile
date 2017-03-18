CXX=g++
CXXFLAGS=-Wall -std=c++11 -pthread -O3 # -D NDEBUG
HEADERS=abssynthe.h logging.h aig.h aiger.h automaton.h
SOURCES=abssynthe.cpp logging.cpp aig.cpp aiger.c aigtocnf.c algos.cpp automaton.cpp
CUDD_PATH=cudd-2.5.1
CUDD_HDRS=$(CUDD_PATH)/include
CUDD_LIBS=$(CUDD_PATH)/obj/libobj.a \
	  $(CUDD_PATH)/cudd/libcudd.a \
	  $(CUDD_PATH)/mtr/libmtr.a \
	  $(CUDD_PATH)/st/libst.a \
	  $(CUDD_PATH)/util/libutil.a \
	  $(CUDD_PATH)/epd/libepd.a
LIBDIR=-L /home/osankur/share/z3-4.4.1/bin
Z3_HDRS=/home/osankur/share/z3-4.4.1/include
abssynthe: $(HEADERS) $(SOURCES) $(CUDD_HDRS) $(CUDD_LIBS)
	$(CXX) $(CXXFLAGS) $(SOURCES) $(CUDD_LIBS) $(LIBDIR) -lz3 -o abssynthe -I $(CUDD_HDRS) -I $(Z3_HDRS) -I./cudd-2.5.1/include
clean:
	rm -f abssynthe
