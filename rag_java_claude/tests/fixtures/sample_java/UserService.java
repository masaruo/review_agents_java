package com.example.service;

import com.example.model.User;
import com.example.repository.UserRepository;
import java.util.Optional;
import java.util.List;

public class UserService {
    private final UserRepository repository;
    private final String serviceName;

    public UserService(UserRepository repository) {
        this.repository = repository;
        this.serviceName = "UserService";
    }

    public User createUser(String name, String email) {
        User user = new User(name, email);
        return repository.save(user);
    }

    public Optional<User> findById(Long id) {
        return repository.findById(id);
    }

    public List<User> findAll() {
        return repository.findAll();
    }

    public void deleteUser(Long id) {
        repository.deleteById(id);
    }
}
