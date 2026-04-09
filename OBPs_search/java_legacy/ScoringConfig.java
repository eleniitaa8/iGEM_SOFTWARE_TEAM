public class ScoringConfig {

    private double pesAfinitat;
    private double pesEspecificitat;
    private double pesEstudis;
    private double kiMaxima;
    private int    maxVOCsAlternatius;

    public static ScoringConfig automatic() {
        ScoringConfig config = new ScoringConfig();
        config.pesAfinitat        = 0.50;
        config.pesEspecificitat   = 0.30;
        config.pesEstudis         = 0.20;
        config.kiMaxima           = 30.0;
        config.maxVOCsAlternatius = 50;
        return config;
    }

    public static ScoringConfig personalitzat(double pesAfinitat, double pesEspecificitat,
                                               double pesEstudis, double kiMaxima,
                                               int maxVOCsAlternatius) {
        double sumaPesos = pesAfinitat + pesEspecificitat + pesEstudis;
        if (Math.abs(sumaPesos - 1.0) > 0.01)
            throw new IllegalArgumentException("Els pesos han de sumar 1.0. Total: " + sumaPesos);
        ScoringConfig config = new ScoringConfig();
        config.pesAfinitat        = pesAfinitat;
        config.pesEspecificitat   = pesEspecificitat;
        config.pesEstudis         = pesEstudis;
        config.kiMaxima           = kiMaxima;
        config.maxVOCsAlternatius = maxVOCsAlternatius;
        return config;
    }

    public double getPesAfinitat()        { return pesAfinitat; }
    public double getPesEspecificitat()   { return pesEspecificitat; }
    public double getPesEstudis()         { return pesEstudis; }
    public double getKiMaxima()           { return kiMaxima; }
    public int    getMaxVOCsAlternatius() { return maxVOCsAlternatius; }

    @Override
    public String toString() {
        return String.format(
            "Pesos → Afinitat=%.0f%% Especif.=%.0f%% Estudis=%.0f%% | Ki maxima=%.1f µM | Max VOCs alt=%d",
            pesAfinitat * 100, pesEspecificitat * 100, pesEstudis * 100,
            kiMaxima, maxVOCsAlternatius);
    }
}
