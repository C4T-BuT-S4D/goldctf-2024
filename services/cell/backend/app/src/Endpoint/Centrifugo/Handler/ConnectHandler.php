<?php

declare(strict_types=1);

namespace App\Endpoint\Centrifugo\Handler;

use RoadRunner\Centrifugo\Payload\ConnectResponse;
use RoadRunner\Centrifugo\Request\Connect;
use RoadRunner\Centrifugo\Request\RequestInterface;
use Spiral\Auth\TokenStorageInterface;
use Spiral\RoadRunnerBridge\Centrifugo\ServiceInterface;

final class ConnectHandler implements ServiceInterface
{
    public function __construct( private readonly TokenStorageInterface $tokenStorage,)
    {

    }
    /**
     * @param Connect $request
     */
    public function handle(RequestInterface $request): void
    {
        try {
//            $userId = null;
//
//            // Authenticate user with a given token from the connection request
//            $authToken = $request->getData()['authToken'] ?? null;
//            if ($authToken !== null) {
//                $token = $this->tokenStorage->load($authToken);
//                if ($token !== null) {
//                    $userId = $token->getPayload()['uid'] ?? null;
//                }
//            }

            $request->respond(
                new ConnectResponse(
                    user: "", // User ID
                    channels: [
                        // List of channels to subscribe to on connect to Centrifugo
                        // 'public',
                    ],
                )
            );
        } catch (\Throwable $e) {
            $request->error($e->getCode(), $e->getMessage());
        }
    }
}
