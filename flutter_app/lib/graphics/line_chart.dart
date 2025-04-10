import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'dart:math' as math;


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


class StandardLineChart extends StatelessWidget {

  final String xAxisText;
  final String yAxisText;
  final List<FlSpot> dataPoints;

  const StandardLineChart(this.xAxisText, this.yAxisText, this.dataPoints, {super.key});

  @override
  Widget build(BuildContext context) {
    return LineChart(
      duration: const Duration(milliseconds: 500), // Increase animation duration
      curve: Curves.easeInOut,
      LineChartData(
          minX: dataPoints.isEmpty ? 0 : dataPoints.first.x,
          maxX: dataPoints.isEmpty ? 5 : (dataPoints.last.x + 1),
          minY: 0,
          maxY: dataPoints.isEmpty ? 5 : dataPoints.map((spot) => spot.y).reduce(math.max) + 1,
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
                reservedSize: 30,
                getTitlesWidget: leftTitleWidgets,
              ),
              axisNameWidget: Container(
                padding: EdgeInsets.only(left: 50.0),
                width: double.infinity,
                child: Text(
                  yAxisText,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.black,
                    fontSize: 16,
                  ),
                ),
              ),
              axisNameSize: 25,
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
                reservedSize: 30,
                getTitlesWidget: leftTitleWidgets,
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
              spots: dataPoints,
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
              show: true,
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