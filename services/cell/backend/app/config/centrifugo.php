<?php

use App\Endpoint\Centrifugo\Handler\ConnectHandler;
use App\Endpoint\Centrifugo\Handler\RPCHandler;
use App\Endpoint\Centrifugo\Handler\SubscribeHandler;
use RoadRunner\Centrifugo\Request\RequestType;

return [
    'services' => [
        RequestType::Connect->value => ConnectHandler::class,
        RequestType::Subscribe->value => SubscribeHandler::class,
        RequestType::RPC->value => RPCHandler::class,
        //...
    ],
    'interceptors' => [
        //...
    ],
];
