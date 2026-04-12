import java.io.FileInputStream;
import java.io.IOException;

public class BuggyClass {
    private String[] items;

    public BuggyClass(int size) {
        items = new String[size];
    }

    // NullPointerException risk: no null check
    public int getLength(String str) {
        return str.length();
    }

    // Resource leak: stream not closed
    public byte[] readFile(String path) throws IOException {
        FileInputStream fis = new FileInputStream(path);
        byte[] data = new byte[fis.available()];
        fis.read(data);
        return data;
    }

    // Array index out of bounds risk
    public String getItem(int index) {
        return items[index];
    }
}
