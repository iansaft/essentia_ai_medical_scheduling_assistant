BEGIN;

DELETE FROM appointment_slots
WHERE
    id IN (
        '8e06b231-a27f-4bf3-bc69-7565f20c3f7d',
        '26036bfd-3ba4-405d-9e7a-4df6a540ee1f',
        '51d9ec84-aa0a-46ca-a37b-4952a5e35cc7',
        'a834893e-8336-4c78-8c27-84e60256e3c7',
        '217c57f6-d78f-475d-8557-975d7af79d81',
        '7d25ff3c-b772-4b73-afa2-794071397b86',
        '7b983580-560d-42d5-a40a-8189b8035dbc',
        '63d4a85a-bf72-414a-a849-e11aedf0be59',
        '3f28f670-d1f2-4279-bad8-a5c3af470764',
        '5c84f94d-07d4-48a0-8e43-a5409af6623c',
        'f9790797-1fef-47ac-9c90-d682a9aaa9d1',
        '2d4a9c21-db19-40a7-a10e-6179921145cd',
        'd59462db-a8f2-425e-9cdc-52c055f08c90'
    );

COMMIT;