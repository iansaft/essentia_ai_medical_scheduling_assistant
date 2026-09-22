BEGIN;

DELETE FROM appointments
WHERE
    id IN (
        '8029d8d3-8fff-4dcc-a2ef-2ae0808bf95e',
        'd6e99970-3b01-43c4-84a9-4042188262be',
        '75adebb0-cff9-4a8c-9dfc-43bc321fabed',
        '607179d5-2c1e-45ca-96bd-4a3593462caa'
    );

COMMIT;