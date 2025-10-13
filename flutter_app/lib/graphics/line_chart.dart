import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:math' as math;

double log10(num x) => math.log(x) / math.ln10;

const double kLogTickStep = 0.02;

Widget leftTitleWidgets(double value, TitleMeta meta) {
  const style = TextStyle(
    color: Colors.black,
    fontSize: 12,
  );
  // Only show integer values to avoid decimal places
  if (value.toInt() == value) {
    return SideTitleWidget(
      meta: meta,
      child: Text('${value.toInt()}', style: style),
    );
  }
  return const SizedBox.shrink();

}

Widget logXAxisTitleWidgets(double value, TitleMeta meta) {
  const labelStyle = TextStyle(
    color: Colors.black,
    fontSize: 12,
    height: 1.0, // tighter line height
  );

  final double interval = meta.appliedInterval ?? kLogTickStep;
  final double halfStep = interval * 0.5;
  final double eps = math.max(1e-6, halfStep - 1e-6);
  final double log5 = math.log(5) / math.ln10; // ~0.69897

  // Render within a short box; draw the tick above using negative positioning.
  Widget buildLabel(String text) {
    const double tickH = 8;
    return SideTitleWidget(
      meta: meta,
      child: SizedBox(
        height: 16, // <= given constraint (~17px), avoids RenderFlex overflow
        child: Stack(
          clipBehavior: Clip.none,
          alignment: Alignment.topCenter,
          children: [
            Positioned(
              top: -tickH, // tick touches the axis line
              child: Container(width: 2, height: tickH, color: Colors.black),
            ),
            Align(
              alignment: Alignment.topCenter,
              child: Text(text, style: labelStyle),
            ),
          ],
        ),
      ),
    );
  }

  final int kRound = value.round();
  if ((value - kRound).abs() < eps) {
    final double realValue = math.pow(10, kRound).toDouble();
    return buildLabel(realValue.toStringAsFixed(0));
  }

  final int kFloor = value.floor();
  if ((value - (kFloor + log5)).abs() < eps) {
    final double realValue = math.pow(10, kFloor).toDouble() * 5.0;
    return buildLabel(realValue.toStringAsFixed(0));
  }

  return const SizedBox.shrink();
}

class StandardLineChart extends StatelessWidget {

  final String xAxisText;
  final String yAxisText;
  final List<FlSpot> dataPoints;

  const StandardLineChart(this.xAxisText, this.yAxisText, this.dataPoints, {super.key});

  @override
  Widget build(BuildContext context) {

    final safeData = dataPoints
        .where((p) => p.x > 0)
        .map((p) => FlSpot(log10(p.x), p.y))
        .toList();

    return LineChart(
      duration: const Duration(milliseconds: 500), // Increase animation duration
      curve: Curves.easeInOut,
      LineChartData(
          minX: safeData.isEmpty ? 0 : safeData.first.x,
          maxX: safeData.isEmpty ? 1 : safeData.last.x + kLogTickStep,
          minY: 0,
          maxY: safeData.isEmpty ? 5 : safeData.map((spot) => spot.y).reduce(math.max) + 1,
          gridData: FlGridData(
            show: false,
            drawVerticalLine: true,
            horizontalInterval: 1,
            verticalInterval: 1,
          getDrawingHorizontalLine: (value) {
            return const FlLine(
              strokeWidth: 1,
            );
            },
            getDrawingVerticalLine: (value) {
              return const FlLine(
                strokeWidth: 1,
              );
            },
          ),
          titlesData: FlTitlesData(
              show: true,
              leftTitles: AxisTitles(
                sideTitles: const SideTitles(
                showTitles: true,
                reservedSize: 22,
                getTitlesWidget: leftTitleWidgets,
              ),
              axisNameWidget: Container(
                padding: EdgeInsets.only(left: 50.0),
                width: double.infinity,
                child: Text(
                  yAxisText,
                  textAlign: TextAlign.center,
                  overflow: TextOverflow.visible,
                  style: TextStyle(
                    color: Colors.black,
                    fontSize: 16,
                    height: 0.99,
                  ),
                ),
              ),
              axisNameSize: 18,
            ),
            rightTitles: AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
            topTitles: AxisTitles(
              sideTitles: SideTitles(showTitles: false),
            ),
            bottomTitles: AxisTitles(
              sideTitles: const SideTitles(
                showTitles: true,
                reservedSize: 22,
                interval: kLogTickStep,
                getTitlesWidget: logXAxisTitleWidgets,
              ),
              axisNameWidget: Container(
                padding: EdgeInsets.only(left: 50.0),
                width: double.infinity,
                child: Text(
                  xAxisText,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.black,
                    fontSize: 16,
                  ),
                ),
              ),
              axisNameSize: 25,
            ),
          ),
          borderData: FlBorderData(
            show: true,
            border: Border.all(
              color: const Color(0xff37434d),
              width: 1,
            ),
          ),
          lineBarsData: [
            LineChartBarData(
              spots: safeData,
            isCurved: false,
            color: Colors.blue,
            barWidth: 2,
            gradient: const LinearGradient(
              colors: [
                Color(0xFF2196F3),
                Color(0xFF50E4FF),
              ],
            ),
            isStrokeCapRound: true,
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                colors: [
                  const Color(0xFF2196F3).withValues(alpha: 0.1),
                  const Color(0xFF50E4FF).withValues(alpha: 0.1),
                ],
              ),
            ),
            dotData: FlDotData(
              show: safeData.length < 20,
              getDotPainter: (spot, percent, barData, index) {
                return FlDotCirclePainter(
                  radius: 4,
                  color: Colors.blue,
                  strokeWidth: 2,
                  strokeColor: Colors.white,
                );
              },
            ),
          ),
        ],
        lineTouchData: LineTouchData(
            touchTooltipData: LineTouchTooltipData(
                getTooltipColor: (touchedSpot) => Colors.black.withValues(alpha: 0.1),
            ),
          getTouchedSpotIndicator: (barData, spotIndexes) {
            return spotIndexes.map((index) {
              return TouchedSpotIndicatorData(
                FlLine(
                  color: Colors.green,
                  strokeWidth: 1,
                ),
                FlDotData(
                  show: true,
                  getDotPainter: (spot, percent, barData, index) {
                    return FlDotCirclePainter(
                      radius: 6, // Larger dot on hover
                      color: Colors.red, // Change color if needed
                      strokeWidth: 2,
                      strokeColor: Colors.white,
                    );
                  },
                ),
              );
            }).toList();
          },
        )
      ),
    );
  }
}