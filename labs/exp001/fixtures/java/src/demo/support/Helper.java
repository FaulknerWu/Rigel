package demo.support;

public final class Helper {
    private Helper() {
    }

    public static String decorate(String value) {
        return "[[" + value + "]]";
    }
}
