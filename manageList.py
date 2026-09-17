"""Command line editor for list.json - the product/vendor watch list.

Examples:
    python manageList.py list
    python manageList.py add-product "Discovery"
    python manageList.py add-vendor "Discovery" "JPC" "https://www.jpc.de/..." --price 24.99
    python manageList.py remove-vendor "Discovery" "JPC"
    python manageList.py remove-product "Discovery"
"""

import argparse
import json
import os
import sys
from parsers.jpc_parser import JPC
from parsers.amazonde_parser import AmazonDE

LIST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "list.json")

# Vendor names the CheckerManager knows how to parse. Anything else is still
# accepted (so the list can be prepared before the parser exists) but warned about.
KNOWN_VENDORS = {JPC.name, AmazonDE.name}


def loadList(path: str = LIST_FILE) -> dict:
    """Return the watch list, creating an empty one on disk if it is missing."""
    if not os.path.exists(path):
        data = {"products": []}
        saveList(data, path)
        print(f"Created {path}")
        return data

    with open(path) as f:
        data = json.load(f)

    data.setdefault("products", [])
    return data


def saveList(data: dict, path: str = LIST_FILE) -> None:
    """Write the list out atomically so a crash cannot leave a half file."""
    tmp = path + ".tmp"
    with open(tmp, mode="w") as f:
        json.dump(data, fp=f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def findProduct(data: dict, name: str) -> dict:
    for product in data["products"]:
        if product["name"].lower() == name.lower():
            return product
    return None


def findVendor(product: dict, name: str) -> dict:
    for vendor in product["vendors"]:
        if vendor["name"].lower() == name.lower():
            return vendor
    return None


def addProduct(data: dict, name: str) -> dict:
    product = findProduct(data, name)
    if product is not None:
        print(f"Product '{product['name']}' already exists.")
        return product

    product = {"name": name, "vendors": []}
    data["products"].append(product)
    print(f"Added product '{name}'.")
    return product


def removeProduct(data: dict, name: str) -> bool:
    product = findProduct(data, name)
    if product is None:
        print(f"No product named '{name}'.")
        return False

    data["products"].remove(product)
    print(f"Removed product '{product['name']}' and its {len(product['vendors'])} vendor(s).")
    return True


def addVendor(data: dict, productName: str, vendorName: str, url: str,
              price: float = 0.0, currency: str = "EUR", create: bool = False) -> bool:
    product = findProduct(data, productName)
    if product is None:
        if not create:
            print(f"No product named '{productName}'. Add it first or pass --create-product.")
            return False
        product = addProduct(data, productName)

    if vendorName not in KNOWN_VENDORS:
        print(f"Warning: no parser registered for vendor '{vendorName}' - "
              f"it will be skipped by the checker. Known: {', '.join(sorted(KNOWN_VENDORS))}")

    vendor = findVendor(product, vendorName)
    if vendor is not None:
        vendor.update({"url": url, "price": float(price), "currency": currency.upper()})
        print(f"Updated vendor '{vendor['name']}' on '{product['name']}'.")
        return True

    product["vendors"].append({
        "name": vendorName,
        "url": url,
        "price": float(price),
        "currency": currency.upper(),
    })
    print(f"Added vendor '{vendorName}' to '{product['name']}'.")
    return True


def removeVendor(data: dict, productName: str, vendorName: str) -> bool:
    product = findProduct(data, productName)
    if product is None:
        print(f"No product named '{productName}'.")
        return False

    vendor = findVendor(product, vendorName)
    if vendor is None:
        print(f"No vendor named '{vendorName}' on '{product['name']}'.")
        return False

    product["vendors"].remove(vendor)
    print(f"Removed vendor '{vendor['name']}' from '{product['name']}'.")
    return True


def printList(data: dict) -> None:
    if not data["products"]:
        print("The watch list is empty.")
        return

    for product in data["products"]:
        print(product["name"])
        if not product["vendors"]:
            print("  (no vendors)")
        for vendor in product["vendors"]:
            print(f"  {vendor['name']}: {vendor['price']} {vendor['currency']}")
            print(f"    {vendor['url']}")


def buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the products and vendors in list.json")
    parser.add_argument("--file", default=LIST_FILE, help="path to the list file (default: list.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="show the current watch list")

    addProductCmd = sub.add_parser("add-product", help="add an empty product")
    addProductCmd.add_argument("product")

    removeProductCmd = sub.add_parser("remove-product", help="remove a product and all its vendors")
    removeProductCmd.add_argument("product")

    addVendorCmd = sub.add_parser("add-vendor", help="add or update a vendor on a product")
    addVendorCmd.add_argument("product")
    addVendorCmd.add_argument("vendor", help=f"one of: {', '.join(sorted(KNOWN_VENDORS))}")
    addVendorCmd.add_argument("url")
    addVendorCmd.add_argument("--price", type=float, default=0.0,
                              help="reference price; 0 means the next run seeds it from the shop")
    addVendorCmd.add_argument("--currency", default="EUR")
    addVendorCmd.add_argument("--create-product", action="store_true",
                              help="create the product if it does not exist yet")

    removeVendorCmd = sub.add_parser("remove-vendor", help="remove a vendor from a product")
    removeVendorCmd.add_argument("product")
    removeVendorCmd.add_argument("vendor")

    return parser


def main(argv: list = None) -> int:
    args = buildParser().parse_args(argv)
    data = loadList(args.file)

    if args.command == "list":
        printList(data)
        return 0

    if args.command == "add-product":
        addProduct(data, args.product)
    elif args.command == "remove-product":
        if not removeProduct(data, args.product):
            return 1
    elif args.command == "add-vendor":
        if not addVendor(data, args.product, args.vendor, args.url,
                         args.price, args.currency, args.create_product):
            return 1
    elif args.command == "remove-vendor":
        if not removeVendor(data, args.product, args.vendor):
            return 1

    saveList(data, args.file)
    return 0


if __name__ == "__main__":
    sys.exit(main())
