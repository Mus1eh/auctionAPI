def owner_auction_closed_email(auction: dict) -> str:
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
