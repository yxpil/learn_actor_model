"""Actor model: actors communicate ONLY via async messages. Each actor has a mailbox
(queue), processes messages one at a time, and can crash and restart without losing queued msgs."""
from collections import deque


class Actor:
    def __init__(self, actor_id, behavior):
        self.id = actor_id
        self.mailbox = deque()
        self.behavior = behavior   # fn(actor_system, sender, msg)
        self.alive = True
        self.processed = 0

    def send(self, msg, sender=None):
        self.mailbox.append((sender, msg))


class ActorSystem:
    def __init__(self):
        self.actors = {}

    def spawn(self, actor_id, behavior):
        a = Actor(actor_id, behavior)
        self.actors[actor_id] = a
        return a

    def tell(self, from_id, to_id, msg):
        a = self.actors.get(to_id)
        if a and a.alive:
            a.send(msg, sender=from_id)

    def deliver_one(self, actor_id):
        """Process the next message in an actor's mailbox (sync, for teaching)."""
        a = self.actors.get(actor_id)
        if not a or not a.alive or not a.mailbox:
            return False
        sender, msg = a.mailbox.popleft()
        try:
            a.behavior(self, sender, msg)
            a.processed += 1
        except Exception as e:
            print(f"  [{actor_id}] crashed on {msg}: {e} -> restarting")
            a.alive = False
            raise
        return True

    def restart(self, actor_id):
        a = self.actors.get(actor_id)
        if a:
            a.alive = True
