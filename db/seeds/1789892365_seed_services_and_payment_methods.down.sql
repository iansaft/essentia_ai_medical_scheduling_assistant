BEGIN;

DELETE FROM payment_methods
WHERE
    id IN (
        'a570a071-95f3-41ee-a8dc-8447ddf026b5',
        'c7a8727c-c8bf-4964-8301-9ccfd3ab09ba',
        'ef967cb7-6a4d-4011-854b-a9408cc8c1d0',
        'e4b8c4d1-80cf-47f2-a271-627623e84be8'
    );

DELETE FROM services
WHERE
    id IN (
        'e2fb5edd-efbd-4d60-9de3-d6650e31562f',
        'b9d24a3f-45eb-48bf-9d48-1f075e4c40a3',
        '6640a42f-830c-4187-aacf-ed576b464b74',
        '93391495-8729-48f7-86e7-b8052b53b868'
    );

COMMIT;