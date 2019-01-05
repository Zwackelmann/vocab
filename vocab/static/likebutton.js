'use strict';

const e = React.createElement;

class LikeButton extends React.Component {
  constructor(props) {
    super(props);
    this.state = { liked: false };
  }

  render() {
    if (this.state.liked) {
      return 'You liked this.';
    } else {
      return e(
        'button',
        { onClick: () => this.setState({ liked: true }) },
        'Like'
      );
    }
  }
}

const domContainer = document.querySelector('#test_container');
ReactDOM.render(e(LikeButton), domContainer);
