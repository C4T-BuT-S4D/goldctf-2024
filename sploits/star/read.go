package main

import (
	"archive/tar"
	"io"
	"os"
)

func main() {
	f, err := os.Open("pwn.tar")
	if err != nil {
		panic(err)
	}

	tr := tar.NewReader(f)
	for {
		hdr, err := tr.Next()
		if err != nil {
			panic(err)
		}
		if hdr.Name == "flag.txt" {
			if _, err := os.Stdout.Write([]byte("flag: ")); err != nil {
				panic(err)
			}
			if _, err := io.Copy(os.Stdout, tr); err != nil {
				panic(err)
			}
			return
		}
	}
}
