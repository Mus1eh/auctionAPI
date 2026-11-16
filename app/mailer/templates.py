def owner_auction_closed_email(auction: dict) -> str:
    # email content for product owner when their auction has ended
    return f"""
Hello,

Your auction has ended.

Auction Details:
-------------------------
Product ID: {auction["product_id"]}
Product Name: {auction["product_name"]}
Auction Started: {auction["auction_started_at"]}
Auction Ended: {auction["auction_ends_at"]}
Total Bids: {auction["bids_count"]}
Final Price: {auction["last_price"]}
Highest Bidder: {auction["highest_bidder_username"] or "No bids"}

Please log in to your account to review the auction.

If bids were placed, you can approve or reject the highest offer.

Auction API Team
"""


def highest_bidder_email(auction: dict) -> str:
    # email content for highest bidder when they win the auction
    return f"""
Hello {auction["highest_bidder_username"]},

Congratulations! You placed the highest bid.

Product: {auction["product_name"]}
Product ID: {auction["product_id"]}
Your Offer: {auction["last_price"]}

The product owner has been notified and will review your offer.

You will receive another email once the owner approves or rejects it.

Auction API Team
"""


def bid_approved_email(product, bidder) -> str:
    # email content for bidder when their bid is approved by the product owner
    return f"""
Hello {bidder.username},

Congratulations! Your bid has been accepted by the product owner.

Product ID: {product.id}
Product Name: {product.name}
Accepted Price: {product.current_price}

Your offer has been approved and the auction is now marked as SOLD.

Auction API Team
"""


def bid_rejected_email(product, bidder) -> str:
    # email content for bidder when their bid is rejected by the product owner
    return f"""
Hello {bidder.username},

The product owner has reviewed your offer.

Unfortunately, your bid was not accepted.

Product ID: {product.id}
Product Name: {product.name}
Your Offer: {product.current_price}

Thank you for participating.

Auction API Team
"""


def account_restore_request_email(user, link: str, expire_minutes: int) -> str:
    # email content with the restore link for a deleted account
    return f"""
Hello {user.username},

You requested to restore your account.

Use this link to restore it:

{link}

This link will expire in {expire_minutes} minutes.

If you did not request this, please ignore this email.

Auction API Team
"""


def restore_user_email(user) -> str:
    # email content confirming the account was restored
    return f"""
Hello {user.username},

Your account has been restored. You can log in again.

If this was not you, please reset your password right away.

Auction API Team
"""
