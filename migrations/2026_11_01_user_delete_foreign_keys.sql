-- LET USERS BE DELETED WITHOUT FOREIGN KEY ERRORS (MATCHES THE ondelete RULES IN app/models.py)
-- requested_by / password reset tokens / product_id -> CASCADE (DELETED WITH THEIR OWNER)
-- reviewed_by -> SET NULL (THE REQUEST STAYS WHEN THE REVIEWING ADMIN IS DELETED)
BEGIN;

ALTER TABLE password_reset_tokens
    DROP CONSTRAINT password_reset_tokens_user_id_fkey,
    ADD CONSTRAINT password_reset_tokens_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE;

ALTER TABLE product_status_requests
    DROP CONSTRAINT product_status_requests_product_id_fkey,
    ADD CONSTRAINT product_status_requests_product_id_fkey
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    DROP CONSTRAINT product_status_requests_requested_by_fkey,
    ADD CONSTRAINT product_status_requests_requested_by_fkey
        FOREIGN KEY (requested_by) REFERENCES users (id) ON DELETE CASCADE,
    DROP CONSTRAINT product_status_requests_reviewed_by_fkey,
    ADD CONSTRAINT product_status_requests_reviewed_by_fkey
        FOREIGN KEY (reviewed_by) REFERENCES users (id) ON DELETE SET NULL;

COMMIT;
