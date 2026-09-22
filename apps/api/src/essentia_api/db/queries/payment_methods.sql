-- name: ListPaymentMethodsByServiceId :many
SELECT pm.id, pm.code, pm.name, pm.description, spm.max_installments, spm.notes
FROM
    service_payment_methods AS spm
    JOIN payment_methods AS pm ON pm.id = spm.payment_method_id
WHERE
    spm.service_id = $1
    AND pm.is_active = TRUE
ORDER BY pm.name;