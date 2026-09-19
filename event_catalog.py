"""The catalog of event types this service knows about.

A closed set: subscribers may only subscribe to these, and producers may
only publish these. Anything else is rejected at the API boundary.

Naming: <domain>.<what_happened> — dot-separated, snake_case.
"""

EVENT_TYPES = {
    # --- stock levels ---
    "stock.below_reorder_point",
    "stock.replenished",
    "stock.adjusted_manually",

    # --- lots & shelf life ---
    "lot.expiring_soon",
    "lot.expired",
    "lot.quarantined",

    # --- receiving ---
    "receipt.completed",
    "receipt.mismatch_detected",

    # --- shipments out ---
    "shipment.dispatched",
    "shipment.delivered",
    "shipment.delayed",

    # --- assets ---
    "asset.serial_registered",
    "asset.decommissioned",
}
