import time
# pip install colorama
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

ROUTE_TIMEOUT = 10  # Seconds until a route is considered stale

class Router:
    def __init__(self, name, link_local_address):
        self.name = name
        self.link_local_address = link_local_address
        self.routing_table = {}
        self.neighbours = {}
        self.updated = True
        self.active = True

    # Add a neighbour to the router
    def add_neighbour(self, neighbour, cost):
        self.neighbours[neighbour.name] = (neighbour, cost)
        self.routing_table[neighbour.name] = {
            "next_hop": neighbour.link_local_address,
            "metric": cost,
            "lifetime": time.time(),
        }

    # Remove a neighbour from the router
    def send_update(self):
        if not self.active:
            return
        for neighbour_name, (neighbour, _) in self.neighbours.items():
            neighbour.receive_update(self.name, self.routing_table)

    # Receive an update from a neighbour
    def receive_update(self, neighbour_name, neighbour_table):
        updated = False
        for destination, data in neighbour_table.items():
            if destination == self.name or neighbour_name not in self.neighbours:
                continue

            neighbour_router, link_cost = self.neighbours[neighbour_name]
            new_cost = link_cost + data["metric"]

            if (destination not in self.routing_table or
                new_cost < self.routing_table[destination]["metric"]):
                self.routing_table[destination] = {
                    "next_hop": neighbour_router.link_local_address,
                    "metric": new_cost,
                    "lifetime": time.time(),
                }
                updated = True
        self.updated = updated

    # Check if the routing table has converged
    def has_converged(self):
        return not self.updated
    
    # Set the router's status to active or inactive
    def set_active(self, status):
        self.active = status
        if not status:
            for destination in self.routing_table:
                self.routing_table[destination] = {
                    "next_hop": None,
                    "metric": float('inf'),
                    "lifetime": time.time(),
                }
            print(f"{Fore.RED}[INFO]{Style.RESET_ALL} Router {self.name} has gone offline!")

    # Print the routing table
    def print_routing_table(self):
        router_color = {
            "A": Fore.RED,
            "B": Fore.GREEN,
            "C": Fore.BLUE,
            "D": Fore.YELLOW
        }
        color = router_color.get(self.name, Fore.WHITE)
        print(f"{color}Routing Table for {self.name}:")
        print(f"{color}-----------------------------------------------------------------")
        print(f"{color}{'Destination Prefix':<20}{'Next Hop':<20}{'Metric':<10}{'Route Lifetime':<15}")
        for destination, data in self.routing_table.items():
            lifetime = "∞" if data["metric"] == float('inf') else round(time.time() - data["lifetime"], 2)
            metric_display = int(data["metric"]) if data["metric"] != float('inf') else 16
            print(f"{color}{destination:<20}{data['next_hop'] or '-':<20}{metric_display:<10}{lifetime:<15}")
        print()

# Expire stale routes based on the routing table and offline routers
def expire_stale_routes(routers, offline_routers):
    current_time = time.time()
    offline_addresses = {r.link_local_address for r in offline_routers}
    for router in routers:
        for destination, route in router.routing_table.items():
            if (route["next_hop"] in offline_addresses and
                (current_time - route["lifetime"]) > ROUTE_TIMEOUT and
                route["metric"] != float('inf')):
                route["metric"] = float('inf')
                route["next_hop"] = None
                route["lifetime"] = current_time
                print(f"{Fore.MAGENTA}[INFO]{Style.RESET_ALL} Route to {destination} expired in Router {router.name} (via offline router)")

# Create router instances
router_a = Router("A", "fe80::1")
router_b = Router("B", "fe80::2")
router_c = Router("C", "fe80::3")
router_d = Router("D", "fe80::4")

# Establish neighbours
router_a.add_neighbour(router_b, 1)
router_b.add_neighbour(router_a, 1)

router_b.add_neighbour(router_c, 2)
router_c.add_neighbour(router_b, 2)

router_a.add_neighbour(router_d, 3)
router_d.add_neighbour(router_a, 3)

router_c.add_neighbour(router_d, 4)
router_d.add_neighbour(router_c, 4)

# Initial tables
router_a.print_routing_table()
time.sleep(2)
router_b.print_routing_table()
time.sleep(2)
router_c.print_routing_table()
time.sleep(2)
router_d.print_routing_table()
time.sleep(2)

# Initial update
router_a.send_update()
router_b.send_update()
router_c.send_update()
router_d.send_update()

# Print routing tables after initial update
print("Routing tables after update:")
time.sleep(2)
router_a.print_routing_table()
time.sleep(2)
router_b.print_routing_table()
time.sleep(2)
router_c.print_routing_table()
time.sleep(2)
router_d.print_routing_table()


print(f"{Fore.MAGENTA}[INFO]{Style.RESET_ALL} The nework is converged!")
time.sleep(2)

# Simulate B going offline
router_b.set_active(False)
router_a.send_update()
router_c.send_update()
router_d.send_update()

# Wait and expire stale routes that depended on B
print("Waiting for routes through Router B to become stale...")
time.sleep(ROUTE_TIMEOUT + 2)

expire_stale_routes(
    routers=[router_a, router_b, router_c, router_d],
    offline_routers=[router_b]
)

# Print routing tables after B goes offline
print("Routing tables after stale routes expired:")
time.sleep(2)
router_a.print_routing_table()
time.sleep(2)
router_c.print_routing_table()
time.sleep(2)
router_d.print_routing_table()

print(f"{Fore.MAGENTA}[INFO]{Style.RESET_ALL} The network has reconverged after changes.")
time.sleep(2)
