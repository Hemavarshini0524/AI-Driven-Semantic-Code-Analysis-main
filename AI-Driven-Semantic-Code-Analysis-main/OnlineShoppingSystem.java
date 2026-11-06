
import java.util.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

// Interface
interface Discountable {
    double calculateDiscount();
}

// Custom exception
class InsufficientStockException extends Exception {
    public InsufficientStockException(String message) {
        super(message);
    }
}

// Abstract base class
abstract class Product {
    protected int productId;
    protected String name;
    protected double price;
    protected int stock;

    public Product(int productId, String name, double price, int stock) {
        this.productId = productId;
        this.name = name;
        this.price = price;
        this.stock = stock;
    }

    public abstract String getCategory();

    public void reduceStock(int quantity)
            throws InsufficientStockException {
        if (quantity > stock) {
            throw new InsufficientStockException(
                "Not enough stock for " + name
            );
        }
        stock -= quantity;
    }

    public void displayProduct() {
        System.out.println(
            productId + " - " + name +
            " | Price: " + price +
            " | Stock: " + stock
        );
    }

    public double getPrice() {
        return price;
    }

    public int getProductId() {
        return productId;
    }

    public String getName() {
        return name;
    }
}

// Inheritance and interface implementation
class Electronics extends Product implements Discountable {
    private int warrantyMonths;

    public Electronics(int id, String name, double price,
                       int stock, int warrantyMonths) {
        super(id, name, price, stock);
        this.warrantyMonths = warrantyMonths;
    }

    @Override
    public String getCategory() {
        return "Electronics";
    }

    @Override
    public double calculateDiscount() {
        return price * 0.10;
    }

    public void displayWarranty() {
        System.out.println("Warranty: " + warrantyMonths + " months");
    }
}

class Clothing extends Product implements Discountable {
    private String size;

    public Clothing(int id, String name, double price,
                    int stock, String size) {
        super(id, name, price, stock);
        this.size = size;
    }

    @Override
    public String getCategory() {
        return "Clothing";
    }

    @Override
    public double calculateDiscount() {
        return price * 0.15;
    }

    public void displaySize() {
        System.out.println("Size: " + size);
    }
}

// Customer class
class Customer {
    private int customerId;
    private String name;
    private String email;
    private List<Order> orders;

    public Customer(int customerId, String name, String email) {
        this.customerId = customerId;
        this.name = name;
        this.email = email;
        this.orders = new ArrayList<>();
    }

    public void addOrder(Order order) {
        orders.add(order);
    }

    public List<Order> getOrders() {
        return orders;
    }

    public int getCustomerId() {
        return customerId;
    }

    public String getName() {
        return name;
    }

    public void displayCustomer() {
        System.out.println(
            "Customer: " + name + " | Email: " + email
        );
    }
}

// Generic repository
class Repository<T> {
    private Map<Integer, T> records = new HashMap<>();

    public void save(int id, T object) {
        records.put(id, object);
    }

    public T findById(int id) {
        return records.get(id);
    }

    public List<T> findAll() {
        return new ArrayList<>(records.values());
    }
}

// Order class
class Order {
    private int orderId;
    private Customer customer;
    private List<Product> products;
    private LocalDateTime orderDate;
    private String status;

    public Order(int orderId, Customer customer) {
        this.orderId = orderId;
        this.customer = customer;
        this.products = new ArrayList<>();
        this.orderDate = LocalDateTime.now();
        this.status = "CREATED";
    }

    public void addProduct(Product product, int quantity)
            throws InsufficientStockException {
        product.reduceStock(quantity);

        for (int i = 0; i < quantity; i++) {
            products.add(product);
        }
    }

    public double calculateTotal() {
        double total = 0;

        for (Product product : products) {
            total += product.getPrice();
        }

        return total;
    }

    public void updateStatus(String status) {
        this.status = status;
    }

    public void displayOrder() {
        System.out.println("Order ID: " + orderId);
        System.out.println("Customer: " + customer.getName());
        System.out.println(
            "Date: " + orderDate.format(
                DateTimeFormatter.ofPattern("dd-MM-yyyy HH:mm")
            )
        );
        System.out.println("Status: " + status);
        System.out.println("Total: " + calculateTotal());
    }

    public int getOrderId() {
        return orderId;
    }
}

// Shopping cart service
class ShoppingCart {
    private Customer customer;
    private List<Product> cartItems;

    public ShoppingCart(Customer customer) {
        this.customer = customer;
        this.cartItems = new ArrayList<>();
    }

    public void addToCart(Product product) {
        cartItems.add(product);
    }

    public void removeFromCart(Product product) {
        cartItems.remove(product);
    }

    public double calculateCartValue() {
        double total = 0;

        for (Product product : cartItems) {
            total += product.getPrice();
        }

        return total;
    }

    public List<Product> getItems() {
        return cartItems;
    }
}

// Payment interface
interface PaymentProcessor {
    boolean processPayment(double amount);
}

// Payment implementation
class CreditCardPayment implements PaymentProcessor {
    private String cardNumber;

    public CreditCardPayment(String cardNumber) {
        this.cardNumber = cardNumber;
    }

    @Override
    public boolean processPayment(double amount) {
        System.out.println(
            "Processing credit card payment of " + amount
        );
        return amount > 0;
    }
}

class UPIPayment implements PaymentProcessor {
    private String upiId;

    public UPIPayment(String upiId) {
        this.upiId = upiId;
    }

    @Override
    public boolean processPayment(double amount) {
        System.out.println(
            "Processing UPI payment of " + amount
        );
        return amount > 0;
    }
}

// Main shopping service
class ShoppingService {
    private Repository<Product> productRepository;
    private Repository<Customer> customerRepository;
    private Repository<Order> orderRepository;

    public ShoppingService() {
        productRepository = new Repository<>();
        customerRepository = new Repository<>();
        orderRepository = new Repository<>();
    }

    public void addProduct(Product product) {
        productRepository.save(
            product.getProductId(), product
        );
    }

    public void registerCustomer(Customer customer) {
        customerRepository.save(
            customer.getCustomerId(), customer
        );
    }

    public Order checkout(
            int orderId,
            Customer customer,
            ShoppingCart cart,
            PaymentProcessor paymentProcessor)
            throws InsufficientStockException {

        Order order = new Order(orderId, customer);

        for (Product product : cart.getItems()) {
            order.addProduct(product, 1);
        }

        double total = order.calculateTotal();

        if (paymentProcessor.processPayment(total)) {
            order.updateStatus("PAID");
            customer.addOrder(order);
            orderRepository.save(orderId, order);
            return order;
        }

        order.updateStatus("PAYMENT_FAILED");
        return order;
    }

    public void displayProducts() {
        for (Product product : productRepository.findAll()) {
            product.displayProduct();
        }
    }

    public void displayOrders() {
        for (Order order : orderRepository.findAll()) {
            order.displayOrder();
        }
    }
}

// Main application
public class OnlineShoppingSystem {

    public static void main(String[] args) {

        ShoppingService service = new ShoppingService();

        try {
            Electronics laptop = new Electronics(
                101, "Laptop", 65000, 10, 24
            );

            Clothing shirt = new Clothing(
                102, "T-Shirt", 1200, 50, "L"
            );

            Customer customer = new Customer(
                1, "Rahul", "rahul@example.com"
            );

            service.addProduct(laptop);
            service.addProduct(shirt);
            service.registerCustomer(customer);

            ShoppingCart cart = new ShoppingCart(customer);
            cart.addToCart(laptop);
            cart.addToCart(shirt);

            PaymentProcessor payment =
                new UPIPayment("rahul@upi");

            Order order = service.checkout(
                5001, customer, cart, payment
            );

            System.out.println("\nORDER DETAILS");
            order.displayOrder();

            System.out.println("\nAVAILABLE PRODUCTS");
            service.displayProducts();

            System.out.println("\nALL ORDERS");
            service.displayOrders();

        } catch (InsufficientStockException error) {
            System.out.println(
                "Shopping error: " + error.getMessage()
            );
        }
    }
}
