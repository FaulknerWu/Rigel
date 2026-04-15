package demo.service;

import demo.api.Greeter;
import demo.base.BaseService;
import demo.support.Helper;

public class GreetingService extends BaseService implements Greeter {
    @Override
    public String compose(String name) {
        return Helper.decorate(normalize(name));
    }
}
