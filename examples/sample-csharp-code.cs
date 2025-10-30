// Sample C# code to demonstrate workflow detection capabilities

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;

namespace SampleApp.Services
{
    /// <summary>
    /// Sample service demonstrating various data workflow patterns
    /// that Workflow Tracker can detect and document.
    /// </summary>
    public class UserService
    {
        private readonly AppDbContext _context;
        private readonly HttpClient _httpClient;
        private readonly IMessageQueue _messageQueue;

        public UserService(AppDbContext context, HttpClient httpClient, IMessageQueue messageQueue)
        {
            _context = context;
            _httpClient = httpClient;
            _messageQueue = messageQueue;
        }

        // DATABASE READ - Will be detected as a database query operation
        public async Task<User> GetUserByIdAsync(int userId)
        {
            return await _context.Users
                .Where(u => u.Id == userId)
                .Include(u => u.Profile)
                .FirstOrDefaultAsync();
        }

        // DATABASE WRITE - Will be detected as a database write operation
        public async Task<User> CreateUserAsync(User user)
        {
            _context.Users.Add(user);
            await _context.SaveChangesAsync();
            return user;
        }

        // API CALL - Will be detected as an HTTP API call
        public async Task<ExternalUserData> FetchExternalUserDataAsync(string userId)
        {
            var response = await _httpClient.GetAsync($"https://api.example.com/users/{userId}");
            response.EnsureSuccessStatusCode();

            return await response.Content.ReadAsAsync<ExternalUserData>();
        }

        // WORKFLOW: API -> Transform -> Database Write
        // This will show as a connected workflow in the visualization
        public async Task SyncUserFromExternalApiAsync(string externalUserId)
        {
            // Step 1: API Call
            var externalData = await _httpClient.GetAsync(
                $"https://api.partner.com/v1/users/{externalUserId}"
            );

            var userData = await externalData.Content.ReadAsAsync<ExternalUserDto>();

            // Step 2: Data transformation
            var user = MapToUser(userData);

            // Step 3: Database write
            _context.Users.Add(user);
            await _context.SaveChangesAsync();

            // Step 4: Message queue (notification)
            await _messageQueue.SendAsync("user-created", new { UserId = user.Id });
        }

        // FILE I/O - Will be detected as file operations
        public async Task ExportUsersToFileAsync(string filePath)
        {
            var users = await _context.Users.ToListAsync();

            var json = JsonSerializer.Serialize(users);
            await File.WriteAllTextAsync(filePath, json);
        }

        // MESSAGE QUEUE - Will be detected as message send operation
        public async Task NotifyUserCreatedAsync(int userId)
        {
            var message = new UserCreatedMessage
            {
                UserId = userId,
                Timestamp = DateTime.UtcNow
            };

            await _messageQueue.SendMessageAsync("user-events", message);
        }

        // COMPLEX WORKFLOW: Multiple database operations with business logic
        public async Task ProcessUserOrderAsync(int userId, Order order)
        {
            // Read user data
            var user = await _context.Users
                .Where(u => u.Id == userId)
                .FirstOrDefaultAsync();

            if (user == null)
                throw new Exception("User not found");

            // Read inventory
            var product = await _context.Products
                .Where(p => p.Id == order.ProductId)
                .FirstOrDefaultAsync();

            // Update inventory (database write)
            product.Stock -= order.Quantity;
            _context.Products.Update(product);

            // Create order record (database write)
            _context.Orders.Add(order);

            // Save all changes
            await _context.SaveChangesAsync();

            // Send notification via message queue
            await _messageQueue.SendMessageAsync("order-processed", new
            {
                UserId = userId,
                OrderId = order.Id
            });

            // Call external payment API
            var paymentResponse = await _httpClient.PostAsync(
                "https://payment.api.com/charge",
                new StringContent(JsonSerializer.Serialize(order.Payment))
            );
        }

        private User MapToUser(ExternalUserDto dto)
        {
            // Data transformation logic
            return new User
            {
                Email = dto.EmailAddress,
                Name = dto.FullName,
                ExternalId = dto.Id
            };
        }
    }

    // Supporting classes
    public class AppDbContext : DbContext
    {
        public DbSet<User> Users { get; set; }
        public DbSet<Product> Products { get; set; }
        public DbSet<Order> Orders { get; set; }
    }

    public class User
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
        public string ExternalId { get; set; }
        public UserProfile Profile { get; set; }
    }

    public class Product
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public int Stock { get; set; }
    }

    public class Order
    {
        public int Id { get; set; }
        public int ProductId { get; set; }
        public int Quantity { get; set; }
        public Payment Payment { get; set; }
    }

    public class UserProfile { }
    public class Payment { }
    public class ExternalUserData { }
    public class ExternalUserDto
    {
        public string Id { get; set; }
        public string EmailAddress { get; set; }
        public string FullName { get; set; }
    }

    public class UserCreatedMessage
    {
        public int UserId { get; set; }
        public DateTime Timestamp { get; set; }
    }

    public interface IMessageQueue
    {
        Task SendAsync(string queue, object message);
        Task SendMessageAsync(string queue, object message);
    }
}
