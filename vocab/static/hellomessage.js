class HelloMessage extends React.Component {
    render() {
        return (
            <div>
                Hello {this.props.name}
            </div>
        );
    }
}

const domContainer = document.querySelector('#test_container');
ReactDOM.render(
  <HelloMessage name="Simon" />,
  domContainer
);
