import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

public class SecurityVulnerable {
    // Hardcoded password - security issue
    private static final String DB_PASSWORD = "admin123";

    private Connection conn;

    // SQL injection vulnerability
    public ResultSet findUser(String username) throws Exception {
        Statement stmt = conn.createStatement();
        String query = "SELECT * FROM users WHERE name = '" + username + "'";
        return stmt.executeQuery(query);
    }

    // Sensitive info in logs
    public void login(String user, String password) {
        System.out.println("Login attempt: user=" + user + " password=" + password);
    }
}
