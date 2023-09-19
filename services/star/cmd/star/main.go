package main

import (
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"

	"star/internal/logging"
	"star/internal/service"

	"github.com/sirupsen/logrus"
	"golang.org/x/net/websocket"
)

func handleConnections(ws *websocket.Conn) {
	pwd, _ := os.Getwd()

	cc := service.NewConnectionContext(ws, filepath.Join(pwd, "data"))
	var msg string
	for {
		err := websocket.Message.Receive(ws, &msg)
		if errors.Is(err, io.EOF) {
			logrus.Debugf("client disconnected")
			break
		}
		if err != nil {
			logrus.Debugf("receiving message: %v", err)
			break
		}
		logrus.Debugf("received message: %s", msg)
		cc.ProcessCommand(msg)
	}
}

func main() {
	logging.Init()

	http.Handle("/ws/", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		r.Header.Set("Origin", "http://"+r.Host)
		websocket.Handler(handleConnections).ServeHTTP(w, r)
	}))

	fmt.Println("http server started on :5555")
	err := http.ListenAndServe(":5555", nil)
	if err != nil {
		fmt.Println("Failed to bind socket")
	}
}
