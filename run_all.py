"""Demo: actor-to-actor messaging; an actor crashes and restarts, mailbox survives."""
from framework.actorsystem import ActorSystem


def order_behavior(sys, sender, msg):
    if msg["type"] == "CreateOrder":
        print(f"  [order] got CreateOrder {msg['order_id']}, ask inventory")
        sys.tell("order", "inventory", {"type": "ReserveStock", "order_id": msg["order_id"]})
    elif msg["type"] == "StockReserved":
        print(f"  [order] stock reserved for {msg['order_id']} → order done")


def inventory_behavior(sys, sender, msg):
    if msg["type"] == "ReserveStock":
        if msg["order_id"] == "o_bad":
            raise RuntimeError("db disconnected")
        print(f"  [inventory] reserved stock for {msg['order_id']}")
        sys.tell("inventory", "order", {"type": "StockReserved", "order_id": msg["order_id"]})


def main():
    sys = ActorSystem()
    sys.spawn("order", order_behavior)
    sys.spawn("inventory", inventory_behavior)

    print("--- Case 1: order actor asks inventory, reply comes back ---")
    sys.tell("client", "order", {"type": "CreateOrder", "order_id": "o_1"})
    sys.deliver_one("order")            # order sends ReserveStock to inventory
    sys.deliver_one("inventory")        # inventory reserves, replies StockReserved
    sys.deliver_one("order")            # order marks done

    print("\n--- Case 2: inventory crashes on a bad order, restarts, mailbox drained ---")
    sys.tell("client", "order", {"type": "CreateOrder", "order_id": "o_good"})
    sys.tell("client", "order", {"type": "CreateOrder", "order_id": "o_bad"})
    sys.tell("client", "order", {"type": "CreateOrder", "order_id": "o_good2"})
    # order mailbox has 3 msgs; deliver them
    for _ in range(3):
        sys.deliver_one("order")
    print("  inventory mailbox size:", len(sys.actors["inventory"].mailbox))
    # inventory processes good (ok), then crashes on bad
    sys.deliver_one("inventory")        # o_good -> ok, replies
    try:
        sys.deliver_one("inventory")    # o_bad -> crash
    except RuntimeError:
        pass
    print("  inventory alive?", sys.actors["inventory"].alive)
    sys.restart("inventory")
    print("  restarted. remaining mailbox:", len(sys.actors["inventory"].mailbox))
    # drain the rest
    while sys.deliver_one("inventory"):
        pass
    while sys.deliver_one("order"):
        pass
    print("  inventory processed total:", sys.actors["inventory"].processed)

    print("\n== all cases done ==")


if __name__ == "__main__":
    main()
