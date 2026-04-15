package demo.base;

public class BaseService {
    protected String normalize(String name) {
        return name.trim().toUpperCase();
    }
}
