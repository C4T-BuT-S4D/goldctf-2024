all:
	g++ -std=c++20 -Wall -O0 \
		-c \
		-I ./src \
		src/main.cpp src/digger/server/*.cpp src/digger/crypto/context.cpp

	g++ -std=c++20 -Wall -O2 \
		-c \
		-I ./src \
		src/digger/crypto/des.cpp

	g++ -o digger *.o

	rm *.o
