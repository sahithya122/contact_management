from flask import Flask, render_template, request, redirect, url_for
app = Flask(__name__)
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True

    def search_prefix(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

class Node:
    def __init__(self, contact):
        self.contact = contact
        self.left = None
        self.right = None

    def insert(self, contact, key=lambda x: x):
        if key(contact) <= key(self.contact):
            if self.left is None:
                self.left = Node(contact)
                self.left.prev = self
            else:
                self.left.insert(contact, key)
        else:
            if self.right is None:
                self.right = Node(contact)
                self.right.prev = self
            else:
                self.right.insert(contact, key)

    def search(self, condition):
        results = []
        if self.left is not None:
            results.extend(self.left.search(condition))
        if condition(self.contact):
            results.append(self.contact)
        if self.right is not None:
            results.extend(self.right.search(condition))
        return results

class Contact:
    def __init__(self, name, phone_number, email):
        self.name = name
        self.phone_number = phone_number
        self.email = email
        self.prev = None
        self.next = None

    def __repr__(self):
        return f"{self.name} ({self.phone_number}) - {self.email}"

class ContactManager:
    def __init__(self):
        self.name_trie = Trie()
        self.phone_bst = None
        self.email_hash = {}

    def add_contact(self, contact):
        self.name_trie.insert(contact.name.lower())

        if self.phone_bst is None:
            self.phone_bst = Node(contact)
        else:
            self.phone_bst.insert(contact, key=lambda x: x.phone_number)

        self.email_hash[contact.email.lower()] = contact

    def search_by_name_prefix(self, prefix):
        node = self.name_trie.search_prefix(prefix.lower())
        if node:
            return [contact.name for contact in self.phone_bst.search(lambda x: x.name.lower().startswith(prefix.lower()))]
        else:
            return []

    def search_by_phone_prefix(self, prefix):
        return [contact.name for contact in self.phone_bst.search(lambda x: x.phone_number.startswith(prefix))]

    def search_by_email_prefix(self, prefix):
        node = self.name_trie.search_prefix(prefix.lower())
        if node:
            return [contact.name for contact in self.phone_bst.search(lambda x: x.email.lower().startswith(prefix.lower()))]
        else:
            return []

    def get_all_contacts(self):
        all_contacts = []
        current = self.phone_bst
        while current is not None:
            all_contacts.append(current.contact)
            current = current.right
        return all_contacts

    def delete_contact(self, email):
        contact = self.email_hash.get(email.lower())
        if contact:
            self.name_trie.insert(contact.name.lower())

            if self.phone_bst is not None:
                self.phone_bst = self._remove_from_bst(self.phone_bst, contact, key=lambda x: x.phone_number)

            del self.email_hash[email.lower()]

            if contact.prev:
                contact.prev.next = contact.next
            if contact.next:
                contact.next.prev = contact.prev

    def _remove_from_bst(self, root, contact, key):
        if root is None:
            return root

        if key(contact) < key(root.contact):
            root.left = self._remove_from_bst(root.left, contact, key)
        elif key(contact) > key(root.contact):
            root.right = self._remove_from_bst(root.right, contact, key)
        else:
            if root.left is None:
                return root.right
            elif root.right is None:
                return root.left

            root.contact = self._min_value_node(root.right).contact
            root.right = self._remove_from_bst(root.right, root.contact, key)

        return root

    def _min_value_node(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current

contact_manager = ContactManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_contact', methods=['POST'])
def add_contact():
    name = request.form['name']
    phone_number = request.form['phone_number']
    email = request.form['email']

    contact = Contact(name, phone_number, email)
    contact_manager.add_contact(contact)

    # Redirect to the index route after adding a contact
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    search_term = request.form['search_term']
    name_results = contact_manager.search_by_name_prefix(search_term)
    phone_results = contact_manager.search_by_phone_prefix(search_term)
    email_results = contact_manager.search_by_email_prefix(search_term)

    return render_template('index.html', name_results=name_results, phone_results=phone_results,
                           email_results=email_results)

@app.route('/delete_contact', methods=['POST'])
def delete_contact():
    email_to_delete = request.form['email_to_delete']
    contact_manager.delete_contact(email_to_delete)
    return redirect(url_for('index'))

@app.route('/view_contacts')
def view_contacts():
    all_contacts = contact_manager.get_all_contacts()
    return render_template('all_contacts.html', all_contacts=all_contacts)

if __name__ == '__main__':
    app.run(debug=True)

