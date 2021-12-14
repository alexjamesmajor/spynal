#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plots   A module of functions for generating data plots and plotting-related utilities

FUNCTIONS
### Plot-generating functions ###
plot_line_with_error_fill   Plots 1d data as line(s) w/ transparent fill(s) to indicate errors
plot_heatmap        Plots 2d data as a heatmap (pseudocolor) plot
plot_lineseries     Plots 2d data as series of offset lines

### Plotting utilities ###
plot_markers        Plots set of markers (eg to mark trial event times) on given axis/es
full_figure         Creates full-screen figure


Created on Tue Nov 23 14:22:47 2021

@author: sbrincat
"""
import numpy as np
import matplotlib.pyplot as plt


# =============================================================================
# Functions to generate specific plot types
# =============================================================================
def plot_line_with_error_fill(x, data, err=None, ax=None, color=None, alpha=0.25, linewidth=1.5,
                              events=None, **kwargs):
    """
    Plots 1d data as line plot(s) +/- error(s) as a semi-transparent fill in given axis using
    matplotlib.pyplot.plot and .fill
    
    Can plot multiple lines/errors in same axis by inputting multiple data series,
    as decribed below.

    lines,patches,ax = plot_line_with_error_fill(x,data,err=None,ax=plt.gca(),color=['C0',...,'CN'],
                                                 alpha=0.25,linewidth=1.5,events=None, **kwargsf)

    ARGS
    x       (n,) array-like. x-axis sampling vector for both data and err.

    data    (n,) | (n_lines,n) array-like. Values to plot on y-axis as line(s) (typically means).
            To plot multiples lines with the same x-axis values, input a 2-d array where
            each row will be plotted as a separate line.

    err     (n,) | (n_lines,n) | (2*n_lines,n) ndarray. Error values (SEM/confints/etc.)
            to plotas semi-transparent fill around line.
            If vector-valued or (n_lines,n) array, errors are treated as 1-sided (like SEMs),
            and data[j,:] +/- err[j,:] is plotted for each line j.
            If given as (2*n_lines,n) array, it's treated as 2-sided [upper; lower] error ranges
            (like confidence intervals), with the odd rows = upper and even rows = lower errors
            corresponding to each line.
            If err=None [default], only the data line(s) are plotted without error fills
            (to simplify calling code with optional errors).

    color   Color specification(s). Color to plot both line(s) and error fill(s) in.
            Default: standard matplotlib color order (['C0',...,'C<n_lines>'])

    alpha   Float, range(0-1). Alpha value for plotting error fill(s). 1=fully opaque, 0=fully
            transparent. Default: 0.25

    linewidth Scalar. Line width to plot data line(s) in. Default: 1.5

    events  Callable | (n_events,) array-like of scalars, 2-tuples, and/or 3-tuples.
            List of event values (eg times) to plot markers on x-axis for
            -or- callable function that will plot the event markers itself.
            Markers plotted underneath line + fill. See plot_markers() for details.

    ACTION
    Generate semi-transparent fill + overlaid line plot in same color, in given axis.

    RETURNS
    lines   List of Line2D objects. ax.plot output. Allows access to line properties of line.
    patches List of Polygon objects. ax.fill output. Allows access to patch properties of fill.
    ax      Axis object. Axis plotted into.
    """
    x = np.asarray(x)
    data = np.asarray(data)
    if data.ndim == 1: data = data[np.newaxis,:] # Convert 1d (n,) data -> (1,n) to simplify code
    n_lines = data.shape[0]

    assert data.ndim == 2, \
        ValueError("data must be 1-d (or 2-d for multiple lines) (%d-d data given)" % data.ndim)
    assert data.shape[1] == len(x), \
        ValueError("data (%d) and x (%d) should have same length" % (data.shape[1],len(x)))

    if err is not None:
        err = np.asarray(err)
        if err.ndim == 1: err = err[np.newaxis,:]

        assert err.shape[1] == len(x), \
            ValueError("err.shape[1] (%d) and x (%d) should have same length" % (err.shape[1],len(x)))
        assert err.shape[0] in [n_lines,2*n_lines], \
            ValueError("err must be input as (n,) vector or (2*n_lines,n) array of upper;lower errors")

        # Convert errors to 2-sided upper and lower error bounds to simplify code
        if err.shape[0] == n_lines: upper, lower = data+err, data-err
        else:                       upper, lower = err[0::2,:], err[1::2,:]

        ylim = (lower.min(), upper.max())

    else:
        ylim = (data.min(), data.max())

    # Default ylim to data range +/- 2.5%
    ylim = (ylim[0]-0.025*np.diff(ylim), ylim[1]+0.025*np.diff(ylim))

    # Set axis to plot into (default to current axis)
    if ax is None: ax = plt.gca()

    # Set defaults for axis parameters
    xlim = kwargs.pop('xlim', (x.min(),x.max()))
    ylim = kwargs.pop('ylim', ylim)
    xlabel = kwargs.pop('xlabel', None)
    ylabel = kwargs.pop('ylabel', None)
    # todo should we allow additional kwargs as input to ax.plot (but what about ax.fill???)
    assert len(kwargs) == 0, \
        TypeError("Incorrect or misspelled variable(s) in keyword args: " +
                    ', '.join(kwargs.keys()))

    # Set plotting colors. If only 1 color input, replicate it for all line plots (eg channels)
    if color is None:
        color = ['C'+str(j) for j in range(n_lines)]
    else:
        color = np.atleast_1d(color)
        if (len(color) == 1) or ((len(color) == 3) and (n_lines != 3)):
            color = np.tile(color, (n_lines,))
        else:
            assert len(color) == n_lines, "color must have single value or 1 value per line (channel)"

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    # Plot event markers (if input)
    if events is not None:
        if callable(events):    events
        else:                   plot_markers(events, axis='x', ax=ax, xlim=xlim, ylim=ylim)

    # Plot line(s) and error fill(s) if input
    lines = []
    patches = []
    for j in range(n_lines):
        line = ax.plot(x, data[j,:], '-', color=color[j], linewidth=linewidth)
        lines.append(line)

        if err is not None:
            patch = ax.fill(np.hstack((x,np.flip(x))),
                            np.hstack((upper[j,:], np.flip(lower[j,:]))),
                            facecolor=color[j], edgecolor=None, alpha=alpha)
            patches.append(patch)

    if xlabel is not None: ax.set_xlabel(xlabel)
    if ylabel is not None: ax.set_ylabel(ylabel)

    return lines, patches, ax


def plot_heatmap(x, y, data, ax=None, clim=None, cmap='viridis', origin='lower', events=None,
                 **kwargs):
    """
    Plots 2d data as a heatmap (aka pseudocolor) plot in given axis using matplotlib.pyplot.imshow

    img,ax = plot_heatmap(x,y,data,ax=plt.gca(),clim=(data.min,data.max),cmap='viridis',
                          origin='lower', events=None,**kwargs)

    ARGS
    x       (n_x,) array-like. Sampling vector for data dimension to be plotted along x-axis

    y       (n_y,) array-like. Sampling vector for data dimension to be plotted along y-axis

    data    (n_y,n_x) ndarray. Data to plot on color axis.  NOTE: Data array must be 2d,
            with data to be plotted on y-axis the first dimension and the x-axis data 2nd.

    ax      Pyplot Axis object. Axis to plot into. Default: plt.gca() (current axis)

    clim    (2,) array-like. [low,high] limits of color axis. Default: [min(data),max(data)]

    cmap    String | Colormap object. Colormap to plot heatmap in, given either as name of
            matplotlib colormap or custom matplotlib.colors.Colormap object instance.
            Default: 'viridis' (perceptually uniform dark-blue to yellow colormap)

    origin  String. Where 1st value in data is plotted along y-axis;'lower'=bottom, 'upper'='top'.
            Default: 'lower'

    events  Callable | (n_events,) array-like of scalars, 2-tuples, and/or 3-tuples.
            List of event values (eg times) to plot markers on x-axis for
            -or- callable function that will plot the event markers itself.
            Markers plotted overlaid on heatmap. See plot_markers() for details.

    **kwargs    Any additional keyword args passed directly into ax.imshow

    ACTIONS
    Plots a heatmap plot in given axis, with given parameters. Unless set in kwargs,
    the aspect ratio is set='auto', and the origin='lower' (ie not upside-down)

    RETURNS
    img     AxesImage object. Output of ax.imshow(). Allows access to image properties.
    ax      Axis object. Axis plotted into.
    """
    x = np.asarray(x)
    y = np.asarray(y)

    assert data.ndim == 2, ValueError("data must be 2-dimensional (%d-d data given)" % data.ndim)
    assert data.shape == (len(y),len(x)), \
        ValueError("data (%d,%d) must have dimensions (len(y),len(x)) = (%d,%d)" \
                    % (*data.shape,len(y),len(x)))

    # Set axis to plot into (default to current axis)
    if ax is None: ax = plt.gca()
    # Default color range to data min/max
    if clim is None: clim = (data.min(), data.max())

    xlim = kwargs.pop('xlim',None)
    ylim = kwargs.pop('ylim',None)
    aspect = kwargs.pop('aspect','auto')

    # Find sampling intervals for x, y axes
    dx      = np.diff(x).mean()
    dy      = np.diff(y).mean()
    # Setting plotting extent for each axis = full sampling range +/- 1/2 sampling interval
    # This allows for viewing the entire cells at the edges of the plot, which sometimes makes
    # a difference for sparsely sampled dimensions
    if xlim is None:    xlim = [x[0]-dx/2, x[-1]+dx/2]
    if ylim is None:    ylim = [y[0]-dy/2, y[-1]+dy/2]

    img = ax.imshow(data, extent=[*xlim,*ylim], vmin=clim[0], vmax=clim[1], cmap=cmap,
                    origin=origin, aspect=aspect, **kwargs)

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    # Have to manually invert y-axis tick labels if plotting w/ origin='upper'
    # if origin == 'upper':
    #     yticks = ax.get_yticks()
    #     idxs = (yticks[0] >= ylim[0]) & (yticks[0] <= ylim[1])
    #     yticks = yticks[0][idxs], np.asarray(yticks[1][idxs])
    #     plt.set_yticks(yticks[0])
    #     plt.set_yticklabels(np.flip(yticks[1]))

    # Plot event markers (if input)
    if events is not None:
        if callable(events):    events
        else:                   plot_markers(events, axis='x', ax=ax, xlim=xlim, ylim=ylim)

    return img, ax


def plot_lineseries(x, y, data, ax=None, scale=1.5, color='C0', origin='upper',
                    events=None, **kwargs):
    """
    Plots 2d data as series of vertically-offset line plots with same x-axis.
    Used for example when plotting time-series traces from multiple electrodes on a linear probe.

    lines,ax = plot_lineseries(x,y,data,scale=1.5,color='C0',origin='upper',
                               events=None, **kwargs)

    ARGS
    x       (n_x,) array-like. Sampling vector for data dimension to be plotted along x-axis.
            This will usually be timepoints.

    y       (n_y,) array-like. Sampling vector for data dimension to be plotted along y-axis.
            Determines what is plotted for y-axis ticks (one at each plotted line).
            This will usually be channel numbers or channel labels.

    data    (n_y,n_x) ndarray. Data to plot as vertically-offset line series. NOTE: Data array
            must be 2d, with data to be plotted on y-axis the first dimension and the x-axis data 2nd.

    ax      Pyplot Axis object. Axis to plot into. Default: plt.gca()

    scale   Float. Scale factor for plotting data. 1 = max range of data extends to next
            offset plotted line, >1 = extends farther. Default: 1.5

    color   Color specification | (n_y,) of Color specifications. Color(s) to use to plot each
            line in line series. Must input 1 value per line OR a single value that will be used
            for ALL lines plotted. Default: 'C0' (blue for all lines)

    origin  String. Where 1st value in data is plotted along y-axis;'lower'=bottom, 'upper'='top'.
            Default: 'upper' (so plot has same order as a probe numbered from topmost contact)

    events  Callable | (n_events,) array-like of scalars, 2-tuples, and/or 3-tuples.
            List of event values (eg times) to plot markers on x-axis for
            -or- callable function that will plot the event markers itself.
            Markers plotted underneath lineseries. See plot_markers() for details.

    **kwargs All other keyword args passed directly to ax.plot()

    ACTION
    Plots line series data into given axes using multiple calls to ax.plot()

    RETURNS
    lines   List of Line2D objects. ax.plot output. Allows access to line properties.
    ax      Pyplot Axis object. Axis for plot
    """
    x = np.asarray(x)
    y = np.asarray(y)
    data = np.asarray(data)
    n_lines = len(y)

    assert data.ndim == 2, ValueError("data must be 2-dimensional (%d-d data given)" % data.ndim)
    assert data.shape == (len(y),len(x)), \
        ValueError("data (%d,%d) must have dimensions (len(y),len(x)) = (%d,%d)" \
                    % (*data.shape,len(y),len(x)))

    if ax is None: ax = plt.gca()

    # Set defaults for axis parameters and line parameters
    xlim = kwargs.pop('xlim', (x.min(),x.max()))
    ylim = kwargs.pop('ylim', (-1,n_lines))
    xlabel = kwargs.pop('xlabel', None)
    ylabel = kwargs.pop('ylabel', None)

    if 'linewidth' not in kwargs: kwargs.update(linewidth=1)

    # Set plotting colors. If only 1 color input, replicate it for all line plots (eg channels)
    color = np.atleast_1d(color)
    if (len(color) == 1) or ((len(color) == 3) and (n_lines != 3)):
        color = np.tile(color, (n_lines,))
    else:
        assert len(color) == n_lines, "color must have single value or 1 value per line (channel)"

    # Scale data so max range of data = <scale>*offset btwn lines on plot
    max_val = np.abs(data).max()
    data = scale * data / max_val

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    # Plot event markers (if input)
    if events is not None:
        if callable(events):    events
        else:                   plot_markers(events, axis='x', ax=ax, xlim=xlim, ylim=ylim)

    # Plot each line plot (eg channel) in data with appropriate offset
    lines = []
    for j in range(n_lines):
        offset = n_lines - (j+1) if origin == 'upper' else j
        tmp_lines = ax.plot(x, data[j,:] + offset, color=color[j], **kwargs)
        lines.append(tmp_lines)

    ax.set_yticks(np.arange(n_lines))
    ax.set_yticklabels(y if origin == 'lower' else np.flip(y))
    if xlabel is not None: ax.set_xlabel(xlabel)
    if ylabel is not None: ax.set_ylabel(ylabel)

    return lines, ax


# =============================================================================
# Plotting utilities
# =============================================================================
def plot_markers(values, axis='x', ax=None, xlim=None, ylim=None,
                 linecolor=[0.50,0.50,0.50], linewidth=0.5,
                 fillcolor=[0.50,0.50,0.50], fillalpha=0.2):
    """
    Plot set of markers (eg to mark trial event times) on given axis/axes

    Single point events should be input as scalars in <values>, and are plotted as
    a single line of given color and width.

    Events extending over a range/duration should be input as 2-length (start,end) tuples,
    in <values>, and are plotted as filled rectangles of given color and alpha (transparency).

    Events that reflect a central value (eg mean) +/- a range or error (eg SDs) should
    be input as 3-length (center-error,center,center+error) tuples in <values>, and are
    plotted as a solid central line with dashed error lines, in the given color and width.

    All marker types extend the full length of the opposing axis.

    NOTE: If limits are explicitly input for the axis the markers are plotted on, any marker fully
    outside of the plot limits will not be plotted, to avoid surprise expansion of the plot limits.

    INPUTS
    values      (n_events,) array-like of scalars, 2-tuples, and/or 3-tuples.
                List of values (eg trial event times) on given axes to plot markers for.
                Each entry in list can be a scalar (plotted as a line), a (start,end)
                2-length tuple (plotted as a filled rectangle), or a (-err,center,+err)
                3-length tuple (plotted as solid line with surrounding dashed lines).

    axis        String. Which axis to plot markers on: 'x'|'y'|'both'.  Default: 'x'

    ACTIONS
    Plots appropriate marker(s) for each value in values

    RETURNS
    ax      Axis object. Axis plotted into.
    handles List of Line2D, Polygon, or lists of Line2D objects. ax.plot/fill outputs for each
            marker plotted, in the same order as input. Allows access to properties of marker
            lines/fills.
    """
    if isinstance(values,float) or isinstance(values,int): values = [values]
    xlim_input = xlim is not None
    ylim_input = ylim is not None
    if ax is None: ax = plt.gca()
    if xlim is None: xlim = ax.get_xlim()
    if ylim is None: ylim = ax.get_ylim()
    xlim = np.reshape(xlim,(2,1))
    ylim = np.reshape(ylim,(2,1))

    axis = axis.lower()
    assert axis in ['x','y','both'], ValueError("axis must be 'x'|'y'|'both'")
    axes = ['x','y'] if axis == 'both' else [axis]

    # Functions to plot lines or fills for each event in list
    def plot_single_line(value, axis):
        """ Plot scalar value as single line extending the length of the opposing axis """
        if axis == 'x':
            lines = ax.plot(np.tile(value,(2,1)), ylim, '-', color=linecolor, linewidth=linewidth)
        elif axis == 'y':
            lines = ax.plot(xlim, np.tile(value,(2,1)), '-', color=linecolor, linewidth=linewidth)

        return lines

    def plot_fill(value, axis):
        if axis == 'x':
            patches = ax.fill([value[0],value[0],value[1],value[1]],
                              [ylim[0],ylim[1],ylim[1],ylim[0]],
                              color=fillcolor, edgecolor=None, alpha=fillalpha)
        elif axis == 'y':
            patches = ax.fill([xlim[0],xlim[1],xlim[1],xlim[0]],
                              [value[0],value[0],value[1],value[1]],
                              color=fillcolor, edgecolor=None, alpha=fillalpha)

        return patches

    def plot_three_lines(value, axis):
        """ Plot 3-tuple as 3 lines (dash,solid,dash) extending length of the opposing axis """
        lines = [None]*3
        if axis == 'x':
            lines[0] = ax.plot(np.tile(value[0],(2,1)), ylim, '--', color=linecolor, linewidth=linewidth)
            lines[1] = ax.plot(np.tile(value[1],(2,1)), ylim, '-', color=linecolor, linewidth=linewidth)
            lines[2] = ax.plot(np.tile(value[2],(2,1)), ylim, '--', color=linecolor, linewidth=linewidth)
        elif axis == 'y':
            lines[0] = ax.plot(xlim, np.tile(value[0],(2,1)), '--', color=linecolor, linewidth=linewidth)
            lines[1] = ax.plot(xlim, np.tile(value[1],(2,1)), '-', color=linecolor, linewidth=linewidth)
            lines[2] = ax.plot(xlim, np.tile(value[2],(2,1)), '--', color=linecolor, linewidth=linewidth)

        return lines


    # Iterate thru each marker value (eg event time) and plot line or fill marker for it
    handles = []
    for value in values:
        if isinstance(value,float) or isinstance(value,int): value = [value]
        value = np.asarray(value)
        if value.shape[0] == 0: continue

        # Iterate thru axes (if > 1) to plot markers on
        for axis in axes:
            # Skip plotting any markers that are entirely out of axis limits
            # Note: Only do this if axis limits are explicitly input, to avoid user confusion
            if (axis == 'x') and xlim_input:
                if (value < xlim[0]).all() or (value > xlim[1]).all(): continue
            elif (axis == 'y') and ylim_input:
                if (value < ylim[0]).all() or (value > ylim[1]).all(): continue

            # Plot lines if only scalar value (eg single unitary event time)
            if len(value) == 1:     handle = plot_single_line(value, axis)
            # Plot fill if there are 2 values (start,end) (eg event of given range or duration)
            elif len(value) == 2:   handle = plot_fill(value, axis)
            # Plot fill if there are 2 values (start,end) (eg event of given range or duration)
            elif len(value) == 3:   handle = plot_three_lines(value, axis)
            else:
                raise ValueError("Each value in values must be scalar|2-tuple|3-tuple (not len=%d)"
                                % len(value))

            handles.append(handle)

    return ax, handles


def full_figure(**kwargs):
    """
    Creates full-screen figure. Wrapper around plt.figure() that sets size to full screen.

    ARGS
    **kwargs    Any keyword args passed directly to plt.figure()

    ACTION      Opens new figure that fills entire screen

    RETURNS
    fig         Figure object. Output of plt.figure()
    """
    if 'frameon' not in kwargs: kwargs.update(frameon=True) # WAS False (changed due to MPL 3.1.0)
    fig = plt.figure(**kwargs)
    maximize_figure()
    return fig


def maximize_figure():
    """
    Maximizes size of current Pyplot figure to fill full screen

    SOURCE  gist.github.com/smidm/d26d34946af1f59446f0
    """
    fig_manager = plt.get_current_fig_manager()
    if hasattr(fig_manager, 'window'): fig_manager.window.showMaximized()