package service

import (
	"fmt"

	"github.com/sirupsen/logrus"
	"golang.org/x/net/websocket"
)

func (cc *ConnectionContext) send(format string, v ...any) {
	msg := fmt.Sprintf(format, v...)
	logrus.Debugf("sending message: %s", msg)
	if err := websocket.Message.Send(cc.conn, msg); err != nil {
		logrus.Debugf("Failed to send message: %s", err)
	}
}

func (cc *ConnectionContext) internalErr(format string, v ...any) {
	msg := fmt.Sprintf(format, v...)
	logrus.Errorf("internal error: %s", msg)
	cc.send("internal error")
}

func (cc *ConnectionContext) externalErr(format string, v ...any) {
	msg := fmt.Sprintf(format, v...)
	logrus.Warnf("external error: %s", msg)
	cc.send("error %s", msg)
}
