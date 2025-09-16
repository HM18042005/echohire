import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Animated container with glass morphism effect
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final double? width;
  final double? height;
  final VoidCallback? onTap;
  final double borderRadius;
  final bool blur;

  const GlassCard({
    super.key,
    required this.child,
    this.padding,
    this.margin,
    this.width,
    this.height,
    this.onTap,
    this.borderRadius = AppTheme.radiusMedium,
    this.blur = true,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      margin: margin,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(borderRadius),
        gradient: LinearGradient(
          colors: [
            AppTheme.cardColor.withOpacity(0.7),
            AppTheme.cardColor.withOpacity(0.3),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        border: Border.all(
          color: Colors.white.withOpacity(0.1),
          width: 1,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(borderRadius),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(borderRadius),
          child: Padding(
            padding: padding ?? const EdgeInsets.all(AppTheme.spaceM),
            child: child,
          ),
        ),
      ),
    );
  }
}

/// Animated button with scale and color transitions
class AnimatedButton extends StatefulWidget {
  final String text;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool isLoading;
  final bool isOutlined;
  final Color? color;
  final Color? textColor;
  final double? width;
  final double? height;

  const AnimatedButton({
    super.key,
    required this.text,
    this.onPressed,
    this.icon,
    this.isLoading = false,
    this.isOutlined = false,
    this.color,
    this.textColor,
    this.width,
    this.height,
  });

  @override
  State<AnimatedButton> createState() => _AnimatedButtonState();
}

class _AnimatedButtonState extends State<AnimatedButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: AppTheme.fastAnimation,
      vsync: this,
    );
    _scaleAnimation = Tween<double>(
      begin: 1.0,
      end: 0.95,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleTapDown(TapDownDetails details) {
    _controller.forward();
  }

  void _handleTapUp(TapUpDetails details) {
    _controller.reverse();
  }

  void _handleTapCancel() {
    _controller.reverse();
  }

  @override
  Widget build(BuildContext context) {
    final isEnabled = widget.onPressed != null && !widget.isLoading;
    final buttonColor = widget.color ?? AppTheme.primaryColor;
    final textColor = widget.textColor ?? AppTheme.textPrimary;

    return GestureDetector(
      onTapDown: isEnabled ? _handleTapDown : null,
      onTapUp: isEnabled ? _handleTapUp : null,
      onTapCancel: isEnabled ? _handleTapCancel : null,
      onTap: isEnabled ? widget.onPressed : null,
      child: AnimatedBuilder(
        animation: _scaleAnimation,
        builder: (context, child) {
          return Transform.scale(
            scale: _scaleAnimation.value,
            child: AnimatedContainer(
              duration: AppTheme.normalAnimation,
              width: widget.width,
              height: widget.height ?? 52,
              decoration: BoxDecoration(
                gradient: widget.isOutlined
                    ? null
                    : LinearGradient(
                        colors: isEnabled
                            ? [buttonColor, buttonColor.withOpacity(0.8)]
                            : [Colors.grey.shade600, Colors.grey.shade700],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                border: widget.isOutlined
                    ? Border.all(color: buttonColor, width: 2)
                    : null,
                borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
                boxShadow: isEnabled && !widget.isOutlined
                    ? [
                        BoxShadow(
                          color: buttonColor.withOpacity(0.3),
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                        ),
                      ]
                    : null,
              ),
              child: Material(
                color: Colors.transparent,
                child: InkWell(
                  borderRadius: BorderRadius.circular(AppTheme.radiusMedium),
                  onTap: isEnabled ? widget.onPressed : null,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppTheme.spaceL,
                      vertical: AppTheme.spaceM,
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (widget.isLoading)
                          SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation<Color>(textColor),
                            ),
                          )
                        else if (widget.icon != null)
                          Icon(
                            widget.icon,
                            color: textColor,
                            size: 20,
                          ),
                        if (widget.icon != null || widget.isLoading)
                          const SizedBox(width: AppTheme.spaceS),
                        if (!widget.isLoading)
                          Text(
                            widget.text,
                            style: TextStyle(
                              color: textColor,
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

/// Animated slide transition wrapper
class SlideInAnimation extends StatefulWidget {
  final Widget child;
  final Duration delay;
  final Offset offset;
  final Duration duration;

  const SlideInAnimation({
    super.key,
    required this.child,
    this.delay = Duration.zero,
    this.offset = const Offset(0, 50),
    this.duration = AppTheme.normalAnimation,
  });

  @override
  State<SlideInAnimation> createState() => _SlideInAnimationState();
}

class _SlideInAnimationState extends State<SlideInAnimation>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<Offset> _slideAnimation;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(duration: widget.duration, vsync: this);
    
    _slideAnimation = Tween<Offset>(
      begin: widget.offset,
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
    ));
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOut,
    ));

    Future.delayed(widget.delay, () {
      if (mounted) {
        _controller.forward();
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Transform.translate(
          offset: _slideAnimation.value,
          child: Opacity(
            opacity: _fadeAnimation.value,
            child: widget.child,
          ),
        );
      },
    );
  }
}

/// Loading shimmer effect
class ShimmerLoading extends StatefulWidget {
  final double width;
  final double height;
  final double borderRadius;

  const ShimmerLoading({
    super.key,
    required this.width,
    required this.height,
    this.borderRadius = AppTheme.radiusSmall,
  });

  @override
  State<ShimmerLoading> createState() => _ShimmerLoadingState();
}

class _ShimmerLoadingState extends State<ShimmerLoading>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat();
    
    _animation = Tween<double>(
      begin: -2.0,
      end: 2.0,
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        return Container(
          width: widget.width,
          height: widget.height,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(widget.borderRadius),
            gradient: LinearGradient(
              colors: [
                AppTheme.surfaceColor,
                AppTheme.surfaceColor.withOpacity(0.5),
                AppTheme.surfaceColor,
              ],
              stops: const [0.0, 0.5, 1.0],
              transform: GradientRotation(_animation.value),
            ),
          ),
        );
      },
    );
  }
}