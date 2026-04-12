package com.example;

import java.util.List;
import java.util.ArrayList;

/**
 * Simple calculator class for testing
 */
public class Calculator {
    private int result;
    private List<Integer> history;

    public Calculator() {
        this.result = 0;
        this.history = new ArrayList<>();
    }

    public int add(int a, int b) {
        int sum = a + b;
        history.add(sum);
        return sum;
    }

    public int subtract(int a, int b) {
        int diff = a - b;
        history.add(diff);
        return diff;
    }

    public int multiply(int a, int b) {
        return a * b;
    }

    public double divide(int a, int b) {
        if (b == 0) {
            throw new ArithmeticException("Division by zero");
        }
        return (double) a / b;
    }

    public List<Integer> getHistory() {
        return history;
    }
}
