package demo;

import demo.service.GreetingService;

public class Application {
    public static void main(String[] args) {
        GreetingService service = new GreetingService();
        System.out.println(service.compose("Rigel"));
    }
}
